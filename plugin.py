import sublime
import sublime_plugin
import subprocess
import threading
import os

print_env = False
print_welcome = True


class ExecuteQldbQueryCommand(sublime_plugin.TextCommand):
    inputs = []
    placeholder_count = 0

    # TODO: autorun SELECT queries when can, show results in popup or side tab

    def run(self, edit):
        # Attempt to find the project root
        project_root = self.find_project_root()

        if not project_root:
            sublime.error_message('Project root not found. Ensure you have a .sublime-project file in your project root.')
            return

        print("[QLDB Client] config.ion found:")
        print(project_root)

        config_ion_path = os.path.join(project_root, 'config.ion')
        if not os.path.exists(config_ion_path):
            sublime.error_message('[QLDB Client] config.ion not found in project root.')
            return

        print("[QLDB Client] Connection configuration file found:")
        print(config_ion_path)

        self.debug_print_config_ion(config_ion_path)

        # Get the first selection (if multiple)
        for region in self.view.sel():
            print("[QLDB Client] Region:")
            print(region)

            if region.empty():
                self.execute_command(selected_text, config_ion_path)
                print("[QLDB Client] Region empty")
                print(region)

            if not region.empty():
                # Capture the selected text
                selected_text = self.view.substr(region)

                if not selected_text.endswith('\n'):
                    selected_text += '\n'

                print("[QLDB Client] Running query:")
                print(selected_text)

                # Run the command in a separate thread to avoid blocking Sublime Text
                thread = threading.Thread(target=self.run_command, args=(selected_text, config_ion_path))
                thread.start()
                break

    def find_project_root(self):
        # Get the first folder in the project, assuming it is the root
        window = sublime.active_window()
        folders = window.folders()
        if folders:
            return folders[0]
        return None

    def run_command(self, command, config_ion_path):
        print("[QLDB Client] run_command:")
        print(command)

        try:
            # TODO: Only show debug output if enabled in settings
            print("[QLDB Client] Initiating qldb shell...")
            print("[QLDB Client] Configuration file:")
            print(config_ion_path)

            # Start the qldb shell
            process = subprocess.Popen(
                [
                    # TODO: fix bugs loading .ion config from project root
                    # TODO: Load from settings
                    # TODO: if config provided, only override --ledger etc when specified in settings and log that this is happening when the config file is also being used

                    'qldb', 
                    # '--config', 'qldb.config.ion', 
                    '--ledger', 'DB_NAME', # Database name, for example 'mavus1''
                    '--region', 'REGION', # AWS Region, for example 'ap-southeast-1'
                    '--profile', 'PROFILE_NAME' # from: aws sso login --profile PROFILE_NAME 
                ],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, universal_newlines=True
            )

            print("[QLDB Client] Process:")
            print(process)

            # Send the command
            process.stdin.write(command + '\n')
            process.stdin.flush()

            # Capture the output
            output, errors = process.communicate()

            print("[QLDB Client] Output:")
            print(output)

            print("[QLDB Client] Errors:")
            print(errors)

            # Close qldb shell
            process.stdin.close()
            process.wait()

            qldb_output = output
            print("-------->", command)
            sublime.active_window().run_command("open_output_in_new_column", {"query": command, "output": qldb_output})

            # Print the output and errors to the Sublime Text console
            sublime.set_timeout(lambda: sublime.status_message("Command Output: " + output), 0)
            if errors:
                sublime.set_timeout(lambda: sublime.status_message("Command Errors: " + errors), 0)
        except Exception as e:
            sublime.set_timeout(lambda e=e: sublime.status_message("Failed to run command: " + str(e)), 0)

    def debug_print_config_ion(self, config_ion_path):
        try:
            with open(config_ion_path, 'r', encoding='utf-8') as file:
                config_contents = file.read()
                print("[QLDB Client] Reading config.ion:\n", config_contents)
        except Exception as e:
            print("[QLDB Client] Failed to read config.ion: " + str(e))

        if (print_env):
            print("\n\n::::::::::::")
            print("\n\nSublime env:")
            print(os.environ)
            print("::::::::::::\n\n")


def plugin_loaded():
    sublime.active_window().run_command("show_panel", {"panel": "console"})

    if (print_welcome):
        print()
        print("  ██████▒░██░    ░██████░▒██████  ")
        print(" ██▓▒░ ██▒██░    ▒██  ▒██▒██ ░▒██ ")
        print(" ██▒░  ██▒██▒    ▒██  ▒██▒██████  ")
        print(" ██▒ ▄▄██▒██▒    ▒██  ▒██▒██ ░▒██ ")
        print("  ██████▒░███████░██████▒▒██████  ")
        print("     ▀▀█░  QLDB Client plugin loaded.")
        print("▒  Highlight/select any PartiQL query and")
        print("█ > [Run QLDB Query]")
        print("▒  to forward it to the QLDB shell for immediate execution.")
        print("░ For CLI based automations:")
        print("░ subl --command execute_qldb_query")
        print()


class OpenOutputInNewColumnCommand(sublime_plugin.WindowCommand):
    def run(self, query="No query", output="No output"):
        title = "[QLDB] " + repr(query)
        new_view = self.window.new_file()
        new_view.set_scratch(True)
        new_view.set_read_only(False)
        new_view.set_name(title)
        new_view.set_syntax_file('Packages/Ion Syntax/Ion.sublime-syntax')

        target_group = len(self.window.get_layout()['cols']) - 2
        self.window.set_view_index(new_view, target_group, 0)

        headers = "// [QLDB] \n"
        headers += "// " + query + '\n'

        output_lines = output.split('\n')
        formatted_lines = [("\n// " + line if "documents in bag" in line else line) for line in output_lines]
        formatted_output = '\n'.join(formatted_lines)

        # Insert the output into the new view
        # Must be run in the UI thread to avoid API misuse errors
        sublime.set_timeout_async(lambda: new_view.run_command("append", {"characters": headers}), 0)
        sublime.set_timeout_async(lambda: new_view.run_command("append", {"characters": formatted_output}), 0)
        sublime.set_timeout_async(lambda: new_view.set_read_only(True), 0)
