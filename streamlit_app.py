import streamlit as st
import subprocess
import json
import tempfile
import os

st.title("Google Maps Scraper UI")

st.write("Enter your scraping parameters below:")

query = st.text_input("Search Query", "restaurants in New York")
max_depth = st.number_input("Maximum Scroll Depth", min_value=1, value=10)
lang_code = st.text_input("Language Code", "en")

st.sidebar.title("Deployment Tools (For Testing)")

if st.sidebar.button("Build Go Executable"):
    st.sidebar.write("Attempting to build Go executable...")
    try:
        build_process = subprocess.Popen(["go", "build", "-o", "google-maps-scraper"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        build_stdout, build_stderr = build_process.communicate()
        if build_process.returncode == 0:
            st.sidebar.success("Go executable built successfully!")
        else:
            st.sidebar.error(f"Go build failed with error code {build_process.returncode}")
            st.sidebar.text("Stderr:")
            st.sidebar.text(build_stderr.decode())
    except FileNotFoundError:
        st.sidebar.error("Error: Go command not found. Make sure Go is installed and in PATH.")
    except Exception as e:
        st.sidebar.error(f"An error occurred during Go build: {e}")

if st.sidebar.button("Make Executable"):
    st.sidebar.write("Attempting to set execute permissions...")
    try:
        chmod_process = subprocess.Popen(["chmod", "+x", "./google-maps-scraper"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        chmod_stdout, chmod_stderr = chmod_process.communicate()
        if chmod_process.returncode == 0:
            st.sidebar.success("Executable permissions set successfully!")
        else:
            st.sidebar.error(f"chmod failed with error code {chmod_process.returncode}")
            st.sidebar.text("Stderr:")
            st.sidebar.text(chmod_stderr.decode())
    except FileNotFoundError:
        st.sidebar.error("Error: chmod command not found. This command is for Linux/Unix-like systems.")
    except Exception as e:
        st.sidebar.error(f"An error occurred during chmod: {e}")


if st.button("Start Scraping"):
    st.write(f"Starting scraping for '{query}'...")

    # Construct the command to run the Go executable
    # Create temporary files for input and output
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".txt") as input_file, \
         tempfile.NamedTemporaryFile(mode='r+', delete=False, suffix=".json") as output_file:

        input_filename = input_file.name
        output_filename = output_file.name

        # Write the query to the input file
        input_file.write(query)
        input_file.flush() # Ensure data is written to the file
        input_file.close() # Close the input file so the Go process can access it

        # Construct the command to run the Go executable
        # Assuming the executable is in the same directory as the script
        command = [
            "./google-maps-scraper",
            "-input", input_filename,
            "-results", output_filename,
            "-c", "1", # Concurrency
            "-depth", str(max_depth),
            "-lang", lang_code,
            "-json", # Output as JSON
        ]

        try:
            # Execute the command
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                st.success("Scraping completed successfully!")
                try:
                    # Read the output from the output file
                    output_file.seek(0) # Go back to the beginning of the file
                    results_content = output_file.read()
                    if results_content:
                        # Assuming the output is JSON lines
                        results = [json.loads(line) for line in results_content.strip().split('\n') if line]
                        st.write("Scraping Results:")
                        st.json(results) # Display results as JSON
                    else:
                        st.warning("Scraping completed, but no results were written to the output file.")

                except json.JSONDecodeError:
                    st.error("Failed to parse JSON output from the scraper.")
                    st.text(results_content) # Display raw output for debugging
                finally:
                    output_file.close() # Close the output file before unlinking
            else:
                st.error(f"Scraping failed with error code {process.returncode}")
                st.text("Stderr:")
                st.text(stderr.decode())

        except FileNotFoundError:
            st.error("Error: Go executable not found. Make sure 'google-maps-scraper' is in the same directory.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            # Clean up temporary files with retry
            import time
            for _ in range(5): # Retry up to 5 times
                try:
                    os.unlink(input_filename)
                    break # Exit loop if successful
                except OSError:
                    time.sleep(0.1) # Wait for 100ms

            for _ in range(5): # Retry up to 5 times
                try:
                    os.unlink(output_filename)
                    break # Exit loop if successful
                except OSError:
                    time.sleep(0.1) # Wait for 100ms
