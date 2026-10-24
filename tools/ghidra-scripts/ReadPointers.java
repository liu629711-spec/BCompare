// Resolve a data location's contents: what it points to, and what its fields hold.
// Usage: -postScript ReadPointers.java <label=address> [<label=address> ...]
//
// `BcAlignLines` dispatches through vtables selected by alignment mode, so the
// algorithm lives behind indirect pointers rather than in the dispatching
// function itself. This resolves those pointers one level (and their first
// entries, which are the virtual methods) so the strategy classes become
// addressable and can be decompiled directly.
// @category REA

import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceManager;

public class ReadPointers extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 2) {
			println("usage: ReadPointers.java <output-path> <label=address> ...");
			return;
		}
		String outputPath = args[0];
		Memory memory = currentProgram.getMemory();
		ReferenceManager references = currentProgram.getReferenceManager();

		int resolved = 0;
		java.io.PrintWriter writer = new java.io.PrintWriter(new FileWriter(outputPath));
		try {
			for (int index = 1; index < args.length; index++) {
				String entry = args[index];
				int separator = entry.indexOf('=');
				if (separator < 0) {
					continue;
				}
				String label = entry.substring(0, separator);
				String hex = entry.substring(separator + 1).replaceFirst("^0x", "");
				Address address = currentProgram.getAddressFactory()
					.getDefaultAddressSpace()
					.getAddress(Long.parseLong(hex, 16));

				writer.println("=== " + label + " @ " + address + " mapped=" +
					memory.contains(address) + " initialized=" + memory.getBlock(address) +
					" ===");
				for (int slot = 0; slot < 12; slot++) {
					Address slotAddress = address.add(slot * 8L);
					long value;
					try {
						value = memory.getLong(slotAddress);
					}
					catch (Exception readFailure) {
						writer.println("  slot " + slot + ": <unreadable: " +
							readFailure.getClass().getSimpleName() + ">");
						continue;
					}
					Address target = slotAddress.getNewAddress(value);
					writer.println(String.format(
						"  slot %2d: %-20s -> %s", slot, "0x" + Long.toHexString(value), target));
					Reference[] refs = references.getReferencesFrom(slotAddress);
					for (Reference reference : refs) {
						writer.println("           ref: " + reference.getToAddress() +
							" (" + reference.getReferenceType() + ")");
					}
					resolved++;
				}
				writer.println();
			}
		}
		finally {
			writer.close();
		}
		println("wrote " + outputPath + " (" + resolved + " slots)");
	}
}
