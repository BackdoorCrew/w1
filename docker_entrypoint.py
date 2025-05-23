# w1/docker_entrypoint.py
import os
import subprocess
import sys

def execute_command(cmd_list, step_name, exit_on_error=True, working_directory=None):
    """
    Executes a command and handles the result, printing stdout/stderr.
    """
    final_cmd_list = [str(c) for c in cmd_list]
    print(f"INFO: docker_entrypoint.py: Attempting to execute {step_name}: {' '.join(final_cmd_list)}")
    sys.stdout.flush() # Ensure log is seen before command execution
    try:
        process = subprocess.Popen(final_cmd_list, cwd=working_directory, stdout=sys.stdout, stderr=sys.stderr)
        process.wait() # Wait for the command to complete

        if process.returncode != 0:
            print(f"ERROR: docker_entrypoint.py: Failed to execute {step_name} (exit code: {process.returncode}).", file=sys.stderr)
            if exit_on_error:
                print(f"ERROR: docker_entrypoint.py: Exiting due to error in {step_name}.", file=sys.stderr)
                sys.exit(process.returncode)
            return False
        print(f"INFO: docker_entrypoint.py: {step_name} executed successfully.")
        sys.stdout.flush() # Ensure success message is logged
        return True
    except FileNotFoundError:
        print(f"ERROR: docker_entrypoint.py: Command '{final_cmd_list[0]}' not found for step {step_name}.", file=sys.stderr)
        if exit_on_error:
            sys.exit(1)
        return False
    except Exception as e:
        print(f"ERROR: docker_entrypoint.py: Unexpected error during {step_name}: {e}", file=sys.stderr)
        if exit_on_error:
            sys.exit(1)
        return False

if __name__ == "__main__":
    print("INFO: docker_entrypoint.py: Python entrypoint script started.")
    sys.stdout.flush()

    # --- Debug: Print critical environment variables at runtime ---
    print("INFO: docker_entrypoint.py: Runtime Environment Variables Check:")
    critical_env_vars = [
        'DJANGO_SETTINGS_MODULE', 'DATABASE_URL', 'SECRET_KEY', 'PORT',
        'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'OPENAI_API_KEY', 
        'DEBUG', 'ALLOWED_HOSTS'
        # Add any other critical vars you want to check
    ]
    for var_name in critical_env_vars:
        var_value = os.environ.get(var_name)
        if var_name in ['SECRET_KEY', 'DATABASE_URL', 'GOOGLE_CLIENT_SECRET', 'OPENAI_API_KEY'] and var_value:
            # Print only a portion of sensitive variables for confirmation
            print(f"INFO: docker_entrypoint.py:   {var_name}=<{var_value[:5]}... (length: {len(var_value)})>")
        else:
            print(f"INFO: docker_entrypoint.py:   {var_name}={var_value}")
    sys.stdout.flush()
    # --- End Debug ---

    print("INFO: docker_entrypoint.py: Proceeding with database migrations...")
    if not execute_command(
        ['python', 'manage.py', 'migrate', '--noinput'],
        step_name="database migrations"
        # exit_on_error is True by default
    ):
        print("ERROR: docker_entrypoint.py: Database migrations failed. Exiting.", file=sys.stderr)
        sys.exit(1) # Exit if migrations fail (redundant due to execute_command default, but explicit)

    print("INFO: docker_entrypoint.py: Proceeding with superuser creation/verification...")
    # It's generally fine to not exit on error for superuser creation,
    # as the app might run fine if the user already exists or if it's a dev convenience.
    execute_command(
        ['python', 'create_dev_admin.py'], # Ensure create_dev_admin.py is in the WORKDIR
        step_name="superuser creation/verification",
        exit_on_error=False 
    )
    
    # Static files should have been collected during the Docker build (RUN python manage.py collectstatic...)
    print("INFO: docker_entrypoint.py: Static files should have been collected during build.")
    sys.stdout.flush()

    # --- Prepare and Execute Gunicorn Command ---
    # The command (like "gunicorn", "w1.wsgi:application", "--workers", "2", etc.)
    # comes from the Dockerfile's CMD instruction, passed as arguments to this script.
    gunicorn_cmd_from_dockerfile = sys.argv[1:] 

    if not gunicorn_cmd_from_dockerfile or gunicorn_cmd_from_dockerfile[0].lower() != "gunicorn":
        print("ERROR: docker_entrypoint.py: Expected Gunicorn command from Dockerfile CMD starting with 'gunicorn'.", file=sys.stderr)
        print(f"ERROR: docker_entrypoint.py: Received CMD: {gunicorn_cmd_from_dockerfile}", file=sys.stderr)
        sys.exit(1)

    port = os.environ.get("PORT")
    if not port:
        print("ERROR: docker_entrypoint.py: $PORT environment variable not set. Railway (or your PaaS) should provide this.", file=sys.stderr)
        # Fallback for local testing if absolutely necessary, but Railway needs $PORT.
        # Consider exiting if port is crucial and not found: sys.exit(1)
        # For Railway, PORT will be set, so this error indicates a platform configuration issue.
        # Your initial logs showed PORT=8080, so this path should not be taken on Railway.
        print("WARNING: docker_entrypoint.py: $PORT not set, Gunicorn might fail or use a default port not accessible externally.", file=sys.stderr)
        sys.exit(1) # Exit if PORT is not defined on Railway

    # Build the final Gunicorn command arguments
    # Start with the Gunicorn executable itself (e.g., "gunicorn")
    final_gunicorn_cmd_args = [gunicorn_cmd_from_dockerfile[0]] 
    
    # Add the WSGI application module (e.g., "w1.wsgi:application")
    # This assumes it's the argument immediately after "gunicorn" in your Dockerfile CMD
    if len(gunicorn_cmd_from_dockerfile) < 2:
        print(f"ERROR: docker_entrypoint.py: WSGI application module not found in CMD: {gunicorn_cmd_from_dockerfile}", file=sys.stderr)
        sys.exit(1)
    final_gunicorn_cmd_args.append(gunicorn_cmd_from_dockerfile[1]) 

    # Add the correct --bind argument using the $PORT from environment
    final_gunicorn_cmd_args.extend(["--bind", f"0.0.0.0:{port}"])

    # Add other options from the Dockerfile CMD, skipping any original --bind and its value
    # This iterates through the *rest* of the CMD arguments (i.e., after "gunicorn" and "w1.wsgi:application")
    i = 2 # Start checking from the third argument of the original CMD
    while i < len(gunicorn_cmd_from_dockerfile):
        current_arg = gunicorn_cmd_from_dockerfile[i]
        if current_arg == "--bind":
            # We've already set our own --bind, so skip this arg and its value from Dockerfile CMD
            i += 2 # Skip current_arg ("--bind") and its value (the next argument)
            continue
        final_gunicorn_cmd_args.append(current_arg)
        i += 1
    
    print(f"INFO: docker_entrypoint.py: Preparing to execute main Gunicorn command: {' '.join(final_gunicorn_cmd_args)}")
    sys.stdout.flush() # Ensure this log message is seen
    
    try:
        # Replace the current process (this script) with Gunicorn.
        # This is important for Gunicorn to be the main process and handle signals correctly.
        os.execvp(final_gunicorn_cmd_args[0], final_gunicorn_cmd_args)
    except FileNotFoundError:
        # This error means the gunicorn executable itself wasn't found.
        print(f"ERROR: docker_entrypoint.py: Gunicorn command '{final_gunicorn_cmd_args[0]}' not found. Ensure Gunicorn is installed in the Docker image's PATH.", file=sys.stderr)
        sys.exit(127) # Standard exit code for command not found
    except Exception as e:
        print(f"ERROR: docker_entrypoint.py: Failed to execute Gunicorn command '{' '.join(final_gunicorn_cmd_args)}': {e}", file=sys.stderr)
        sys.exit(1) # Generic error for other exec issues

    # This part of the script should ideally not be reached if os.execvp is successful,
    # as execvp replaces the current process.
    print("ERROR: docker_entrypoint.py: os.execvp failed to replace the current process. This indicates a severe issue with Gunicorn startup.", file=sys.stderr)
    sys.exit(1)