import sublime
import sublime_plugin
import subprocess
import threading
import os

class ExecuteQldbQueryCommand(sublime_plugin.TextCommand):
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
            print("[QLDB Client] Initiating qldb shell...")
            print("[QLDB Client] Configuration file:")
            print(config_ion_path)
            # Start the qldb shell as a subprocess (adjust command as necessary)
            print("var")
            print(config_ion_path)
            print("/Users/martinkruusement/Projektid/mascon/api/config.ion")
            print("raw")
            process = subprocess.Popen(
                        [
                            'qldb', 
                            # '--config', '/Users/martinkruusement/Projektid/mascon/api/config.ion',
                            '--region', 'ap-southeast-1',
                            '--ledger', 'mavus0',
                            '--profile', 'nitram'
                        ],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, universal_newlines=True)

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

            # Ensure to close the process
            process.stdin.close()
            process.wait()

            qldb_output = "[QLDB]\n" + output
            # write_to_output_panel(sublime.active_window(), qldb_output)
            # sublime.active_window().run_command("qldb_output_tab", {"text": qldb_output})
            sublime.active_window().run_command("open_output_in_new_column", {"text": qldb_output})

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


def plugin_loaded():
    sublime.active_window().run_command("show_panel", {"panel": "console"})
    print("RunQldbCommand plugin loaded. Select a command and run 'run_qldb_command' from the console.")


class QldbOutputTabCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        # Create a new file/tab in the current window
        new_view = self.view.window().new_file()
        
        # Optional: Set syntax for better text formatting (e.g., JSON, XML)
        # new_view.set_syntax_file('Packages/JavaScript/JSON.sublime-syntax')
        
        # Disable editing in the new view
        new_view.set_read_only(True)
        
        # Set the name of the new tab (does not save the file)
        new_view.set_name("QLDB Output")
        
        # Write the text to the new tab
        new_view.insert(edit, 0, text)
        
        # Focus the new tab
        self.view.window().focus_view(new_view)


class OpenOutputInNewColumnCommand(sublime_plugin.WindowCommand):
    def run(self, text="QLDX"):
        # The layout setup remains the same as before...

        # After creating the new view and setting it up:
        new_view = self.window.new_file()
        new_view.set_name("QLDB Output")
        new_view.set_read_only(False)  # Temporarily allow writing
        new_view.set_syntax_file('Packages/Ion Syntax/Ion.sublime-syntax')


        # Move the new view to the desired group (column)
        target_group = len(self.window.get_layout()['cols']) - 2
        self.window.set_view_index(new_view, target_group, 0)

        # Insert the text into the new view
        # Must be run in the UI thread to avoid API misuse errors
        sublime.set_timeout_async(lambda: new_view.run_command("append", {"characters": text}), 0)

        # Optionally set the view to read-only after inserting the text
        # new_view.set_read_only(True)