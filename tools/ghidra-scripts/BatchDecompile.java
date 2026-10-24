// Decompile many functions in one headless run.
// Usage: -postScript BatchDecompile.java <output-directory> <address-file>
//
// The address file holds one entry per line: an address or symbol name, optionally
// followed by a tab and a note used in the output header. Starting one JVM for a
// whole batch keeps the per-function cost near the decompile itself rather than
// the ~8 s project-open overhead.
// @category REA

import java.io.FileWriter;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;

public class BatchDecompile extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 2) {
			println("usage: BatchDecompile.java <output-directory> <address-file>");
			return;
		}
		String outputDirectory = args[0];
		String addressFile = args[1];

		List<String> lines = Files.readAllLines(Paths.get(addressFile));
		FunctionManager functions = currentProgram.getFunctionManager();

		DecompInterface decompiler = new DecompInterface();
		decompiler.openProgram(currentProgram);

		int written = 0;
		int failed = 0;
		try (PrintWriter index = new PrintWriter(
			new FileWriter(Paths.get(outputDirectory, "_index.tsv").toFile()))) {
			index.println("address\tname\tsize\tsignature\tfile");

			for (String line : lines) {
				String trimmed = line.trim();
				if (trimmed.isEmpty() || trimmed.startsWith("#")) {
					continue;
				}
				String[] parts = trimmed.split("\t");
				String target = parts[0].trim();
				String note = parts.length > 1 ? parts[1].trim() : "";

				Function function = resolve(functions, target);
				if (function == null) {
					println("unresolved: " + target);
					failed++;
					continue;
				}

				String fileName = function.getEntryPoint() + ".c";
				DecompileResults results = decompiler.decompileFunction(function, 600, monitor);
				try (PrintWriter writer = new PrintWriter(
					new FileWriter(Paths.get(outputDirectory, fileName).toFile()))) {
					writer.println("function: " + function.getName());
					writer.println("entry: " + function.getEntryPoint());
					writer.println("body_size: " + function.getBody().getNumAddresses());
					writer.println("signature: " + function.getPrototypeString(false, false));
					if (!note.isEmpty()) {
						writer.println("note: " + note);
					}
					writer.println();
					if (!results.decompileCompleted()) {
						writer.println("decompile failed: " + results.getErrorMessage());
					}
					else {
						writer.println(results.getDecompiledFunction().getC());
					}
				}
				index.println(
					function.getEntryPoint() + "\t" +
					function.getName() + "\t" +
					function.getBody().getNumAddresses() + "\t" +
					function.getPrototypeString(false, false) + "\t" +
					fileName);
				written++;
			}
		}
		decompiler.dispose();
		println("decompiled " + written + " functions, " + failed + " unresolved");
	}

	private Function resolve(FunctionManager functions, String target) {
		if (target.startsWith("FUN_") || !target.matches(".*[g-zG-Z_].*")) {
			// numeric or FUN_-prefixed: treat as an address
			String hex = target.replaceFirst("^FUN_", "").replaceFirst("^0[xX]", "");
			try {
				Address address = currentProgram.getAddressFactory()
					.getDefaultAddressSpace()
					.getAddress(Long.parseLong(hex, 16));
				Function containing = functions.getFunctionContaining(address);
				if (containing != null) {
					return containing;
				}
				return functions.getFunctionAt(address);
			}
			catch (NumberFormatException exception) {
				return null;
			}
		}
		for (Function function : functions.getFunctions(true)) {
			if (function.getName().equals(target)) {
				return function;
			}
		}
		return null;
	}
}
