import asyncio
import copy
from cover_agent.AICaller import AICaller
from cover_agent.lsp_logic.utils.utils_context import analyze_context, find_test_file_context, \
    initialize_language_server
from cover_agent.utils import parse_args_full_repo, find_test_files
from cover_agent.CoverAgent import CoverAgent


async def run():
    args = parse_args_full_repo()

    # scan the project directory for test files
    test_files = find_test_files(args)
    print(f"Test files found:\n{''.join([f'{f}\n' for f in test_files])}")

    # initialize the language server
    print("\nInitializing language server...")
    lsp = await initialize_language_server(args)

    # start the language server
    async with lsp.start_server():
        print("LSP server initialized.")

        ai_caller = AICaller(model=args.model)

        # main loop for analyzing test files
        for test_file in test_files:
            # Find the context files for the test file
            context_files = await find_test_file_context(args, lsp, test_file)
            print(f"Context files for test file '{test_file}':\n{''.join([f'{f}\n' for f in context_files])}\n")

            # Analyze the test file against the context files
            print("\nAnalyzing test file against context files...")
            source_file, context_files_include = await analyze_context(test_file, context_files, args, ai_caller)

            if source_file:
                # Run the CoverAgent for the test file
                args_copy = copy.deepcopy(args)
                args_copy.source_file_path = source_file
                args_copy.test_file_path = test_file
                args_copy.included_files = context_files_include
                agent = CoverAgent(args_copy)
                agent.run()


if __name__ == "__main__":
    asyncio.run(run())
