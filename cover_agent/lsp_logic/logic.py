import os

from cover_agent.lsp_logic.utils.utils import uri_to_path, is_forbidden_directory


async def get_direct_context(captures, language, lsp, project_dir, rel_file, target_file):
    skip_found_symbols = True
    context_files = set()
    context_symbols = set()
    context_symbols_and_files = set()
    for ref in captures:
        name_symbol = str(ref[0].text.decode())
        if name_symbol in context_symbols and skip_found_symbols:
            continue
        # getting direct context - which files are referenced by the target file
        try:
            symbol_definition = await lsp.request_definition(rel_file,
                                                             line=ref[0].start_point[0],
                                                             column=ref[0].start_point[1])
            # sleep(0.01)
        except:
            symbol_definition = []
        for d in symbol_definition:
            line = ref[0].start_point[0]
            d_path = uri_to_path(d['uri'])
            rel_d_path = os.path.relpath(d_path, project_dir)
            if (name_symbol, rel_d_path) in context_symbols_and_files and skip_found_symbols:
                continue
            if d_path != target_file:
                if project_dir not in d_path:
                    continue
                if not is_forbidden_directory(d_path, language):
                    print(f"Context definition: \'{name_symbol}\' at line {line} from file \'{rel_d_path}\'")
                    context_files.add(d_path)
                    context_symbols.add(name_symbol)
                    context_symbols_and_files.add((name_symbol, rel_d_path))
    return context_files, context_symbols


async def get_reverse_context(captures, lsp, project_dir, rel_file, target_file):
    skip_found_symbols = True
    reverse_context_files = set()
    reverse_context_symbols = set()
    reverse_context_symbols_and_files = set()
    for ref in captures:
        symbol_name = str(ref[0].text.decode())
        if symbol_name in reverse_context_symbols and skip_found_symbols:
            continue
        if 'name.definition' not in ref[1]:  # only consider definition symbols for reverse context
            continue
        # getting reverse context - which files reference the target file
        try:
            symbol_references = await lsp.request_references(rel_file,
                                                             line=ref[0].start_point[0],
                                                             column=ref[0].start_point[1])
        except:
            symbol_references = []
        # sleep(0.01)
        for r in symbol_references:
            ref_path = uri_to_path(r['uri'])
            rel_ref_path = os.path.relpath(ref_path, project_dir)
            if (symbol_name, rel_ref_path) in reverse_context_symbols_and_files and skip_found_symbols:
                continue
            if project_dir not in ref_path:
                continue
            if ref_path != target_file:
                if 'node_modules' not in ref_path:
                    line = ref[0].start_point[0]
                    print(
                        f"Reverse Context definition: \'{symbol_name}\' at line {line}, used by file \'{rel_ref_path}\'")
                    reverse_context_files.add(ref_path)
                    reverse_context_symbols.add(symbol_name)
                    reverse_context_symbols_and_files.add((symbol_name, rel_ref_path))
    return reverse_context_files, reverse_context_symbols
