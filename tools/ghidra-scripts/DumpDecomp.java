// Decompile one function from the active program and write the C source to a file.
// Usage: -postScript DumpDecomp.java <address> <output-path>
// Runs against a persistent Ghidra project, so auto-analysis is paid once and
// every later invocation answers immediately.
// @category REA

import java.io.FileWriter;
import java.io.PrintWriter;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;

public class DumpDecomp extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 2) {
			println("usage: DumpDecomp.java <address> <output-path>");
			return;
		}
		String addressText = args[0];
		String outputPath = args[1];

		Address address = currentProgram.getAddressFactory()
			.getDefaultAddressSpace()
			.getAddress(Long.parseLong(addressText.replaceFirst("^0[xX]", ""), 16));

		FunctionManager functions = currentProgram.getFunctionManager();
		Function function = functions.getFunctionContaining(address);
		if (function == null) {
			println("no function contains " + addressText);
			try (PrintWriter writer = new PrintWriter(new FileWriter(outputPath))) {
				writer.println("no function contains " + addressText);
			}
			return;
		}

		DecompInterface decompiler = new DecompInterface();
		decompiler.openProgram(currentProgram);

		DecompileResults results = decompiler.decompileFunction(function, 300, monitor);
		try (PrintWriter writer = new PrintWriter(new FileWriter(outputPath))) {
			writer.println("function: " + function.getName());
			writer.println("entry: " + function.getEntryPoint());
			writer.println("body_size: " + function.getBody().getNumAddresses());
			writer.println("signature: " + function.getPrototypeString(false, false));
			writer.println();
			if (!results.decompileCompleted()) {
				writer.println("decompile failed: " + results.getErrorMessage());
			}
			else {
				writer.println(results.getDecompiledFunction().getC());
			}
		}
		decompiler.dispose();
		println("wrote " + outputPath + " for " + function.getName());
	}
}
