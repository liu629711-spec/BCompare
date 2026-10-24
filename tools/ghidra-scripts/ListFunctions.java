// Export every function's entry point, name, and size to a TSV file.
// Usage: -postScript ListFunctions.java <output-path>
// Runs against the persistent project so the listing survives between queries.
// @category REA

import java.io.FileWriter;
import java.io.PrintWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.FunctionManager;

public class ListFunctions extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 1) {
			println("usage: ListFunctions.java <output-path>");
			return;
		}

		FunctionManager functions = currentProgram.getFunctionManager();
		FunctionIterator iterator = functions.getFunctions(true);
		int count = 0;
		int named = 0;
		try (PrintWriter writer = new PrintWriter(new FileWriter(args[0]))) {
			writer.println("entry\tname\tsize\tsignature");
			for (Function function : iterator) {
				count++;
				String name = function.getName();
				if (!name.startsWith("FUN_")) {
					named++;
				}
				writer.println(
					function.getEntryPoint() + "\t" +
					name + "\t" +
					function.getBody().getNumAddresses() + "\t" +
					function.getPrototypeString(false, false));
			}
		}
		println("exported " + count + " functions (" + named + " with real names) to " + args[0]);
	}
}
