// Build a BC string-to-function index in one pass over the analyzed program.
// Usage: -postScript BuildStringIndex.java <output-path> [min-length]
//
// BC ships without symbols, so string references are the practical entry point
// into its code. This walks every defined string, finds the functions that
// reference it, and writes one TSV row per (string, function) pair. Running it
// against a persistent project means the walking cost is paid once and the
// result becomes a reusable lookup table.
// @category REA

import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.HashSet;
import java.util.Set;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.data.DataUtilities;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.DataIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;

public class BuildStringIndex extends GhidraScript {

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 1) {
			println("usage: BuildStringIndex.java <output-path> [min-length]");
			return;
		}
		String outputPath = args[0];
		int minLength = args.length > 1 ? Integer.parseInt(args[1]) : 6;

		Listing listing = currentProgram.getListing();
		ReferenceManager references = currentProgram.getReferenceManager();
		DataIterator dataIterator = listing.getDefinedData(true);

		int stringCount = 0;
		int pairCount = 0;
		int unresolved = 0;

		try (PrintWriter writer = new PrintWriter(new FileWriter(outputPath))) {
			writer.println("string_address\tstring\tfunction_entry\tfunction_name");

			for (Data data : dataIterator) {
				if (monitor.isCancelled()) {
					break;
				}
				Object value = data.getValue();
				if (!(value instanceof String)) {
					continue;
				}
				String text = ((String) value).trim();
				if (text.length() < minLength) {
					continue;
				}
				// Keep rows single-line so the TSV stays parseable.
				text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ");
				if (text.length() > 200) {
					text = text.substring(0, 200);
				}
				stringCount++;

				Address stringAddress = data.getAddress();
				ReferenceIterator incoming = references.getReferencesTo(stringAddress);
				Set<String> seenFunctions = new HashSet<>();
				boolean found = false;
				for (Reference reference : incoming) {
					Address from = reference.getFromAddress();
					Function function = getFunctionContaining(from);
					if (function == null) {
						continue;
					}
					String entry = function.getEntryPoint().toString();
					if (!seenFunctions.add(entry)) {
						continue;
					}
					writer.println(stringAddress + "\t" + text + "\t" + entry + "\t" + function.getName());
					pairCount++;
					found = true;
				}
				if (!found) {
					unresolved++;
				}
			}
		}
		println("strings=" + stringCount + " pairs=" + pairCount + " unreferenced=" + unresolved);
	}
}
