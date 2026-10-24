// Resolve a chain of pointers starting at a .text address.
// Usage: -postScript FollowPointers.java <output-path> <address> [<address> ...]
//
// `BcAlignLines` loads a class-reference constant and hands it to the allocator,
// which means the address in the listing is a *variable* holding a pointer, not
// the vtable itself. This follows that indirection explicitly and reports what
// each level contains, including the first virtual method slots, so the strategy
// classes become decompilable targets.
//
// Every read is guarded: .bss regions are mapped but unreadable, and an
// unguarded MemoryException aborts the whole script.
// @category REA

import java.io.FileWriter;
import java.io.PrintWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.Memory;

public class FollowPointers extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 2) {
			println("usage: FollowPointers.java <output-path> <address> ...");
			return;
		}
		Memory memory = currentProgram.getMemory();
		PrintWriter writer = new PrintWriter(new FileWriter(args[0]));
		try {
			for (int index = 1; index < args.length; index++) {
				String hex = args[index].replaceFirst("^0[xX]", "");
				Address base = currentProgram.getAddressFactory()
					.getDefaultAddressSpace()
					.getAddress(Long.parseLong(hex, 16));

				writer.println("=== follow " + args[index] + " ===");
				Address current = base;
				for (int level = 0; level < 3; level++) {
					long value = readOrReport(writer, memory, current, "level " + level);
					if (value == 0) {
						break;
					}
					Address target = current.getNewAddress(value);
					writer.println("  -> " + target + describe(memory, target));
					// Dump the first several pointer slots, which are the vtable entries.
					for (int slot = 0; slot < 10; slot++) {
						Address slotAddress = target.add(slot * 8L);
						long entry = readOrReport(writer, memory, slotAddress, "  vtable[" + slot + "]");
						if (entry == 0) {
							continue;
						}
						Address method = slotAddress.getNewAddress(entry);
						writer.println("       vtable[" + slot + "] = " + method +
							describe(memory, method));
					}
					current = target;
				}
				writer.println();
			}
		}
		finally {
			writer.close();
		}
		println("wrote " + args[0]);
	}

	private long readOrReport(PrintWriter writer, Memory memory, Address address, String label) {
		try {
			return memory.getLong(address);
		}
		catch (Exception failure) {
			writer.println("  " + label + " @ " + address + " <unreadable: " +
				failure.getClass().getSimpleName() + ">");
			return 0;
		}
	}

	private String describe(Memory memory, Address address) {
		boolean mapped = memory.contains(address);
		if (!mapped) {
			return " <unmapped>";
		}
		boolean executable = memory.getBlock(address).isExecute();
		return executable ? " <code>" : " <data>";
	}
}
