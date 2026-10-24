// Dump instruction listings for several functions in one headless run.
// Usage: -postScript DumpAsm.java <output-directory> <address-file>
// @category REA

import java.io.FileWriter;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;

public class DumpAsm extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 2) {
			println("usage: DumpAsm.java <output-directory> <address-file>");
			return;
		}
		String outputDirectory = args[0];
		String addressFile = args[1];

		List<String> lines = Files.readAllLines(Paths.get(addressFile));
		FunctionManager functions = currentProgram.getFunctionManager();

		int written = 0;
		for (String line : lines) {
			String trimmed = line.trim();
			if (trimmed.isEmpty() || trimmed.startsWith("#")) {
				continue;
			}
			String hex = trimmed.replaceFirst("^FUN_", "").replaceFirst("^0[xX]", "");
			Address address = currentProgram.getAddressFactory()
				.getDefaultAddressSpace()
				.getAddress(Long.parseLong(hex, 16));
			Function function = functions.getFunctionContaining(address);
			if (function == null) {
				function = functions.getFunctionAt(address);
			}
			if (function == null) {
				println("unresolved: " + trimmed);
				continue;
			}
			String fileName = function.getEntryPoint() + ".asm";
			try (PrintWriter writer = new PrintWriter(
				new FileWriter(Paths.get(outputDirectory, fileName).toFile()))) {
				writer.println("function: " + function.getName());
				writer.println("entry: " + function.getEntryPoint());
				writer.println();
				InstructionIterator instructions =
					currentProgram.getListing().getInstructions(function.getBody(), true);
				while (instructions.hasNext()) {
					Instruction instruction = instructions.next();
					writer.println(instruction.getAddress() + "  " + instruction.toString());
				}
			}
			println("wrote " + fileName);
			written++;
		}
		println("dumped " + written + " function listings");
	}
}
