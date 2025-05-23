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
    try:
        # Using Popen and communicating can help capture output for debugging if needed,
        # but for simple execution and relying on direct stdout/stderr, wait() is fine.
        process = subprocess.Popen(final_cmd_list, cwd=working_directory, stdout=sys.stdout, stderr=sys.stderr)
        process.wait()

        if process.returncode != 0:
            print(f"ERROR: docker_entrypoint.py: Failed to execute {step_name} (exit code: {process.returncode}).", file=sys.stderr)
            if exit_on_error:
                print(f"ERROR: docker_entrypoint.py: Exiting due to error in {step_name}.", file=sys.stderr)
                sys.exit(process.returncode)
            return False
        print(f"INFO: docker_entrypoint.py: {step_name} executed successfully.")
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
    sys.stdout.flush() # Ensure immediate output

    # --- Debug: Print critical environment variables at runtime ---
    print("INFO: docker_entrypoint.py: Runtime Environment Variables Check:")
    critical_env_vars = [
        'DJANGO_SETTINGS_MODULE', 'DATABASE_URL', 'SECRET_KEY', 'PORT',
        'GOOGLE_CLIENT_ID', 'OPENAI_API_KEY', 'DEBUG', 'ALLOWED_HOSTS'
    ]
    for var_name in critical_env_vars:
        var_value = os.environ.get(var_name)
        if var_name in ['SECRET_KEY', 'DATABASE_URL', 'GOOGLE_CLIENT_SECRET', 'OPENAI_API_KEY'] and var_value:
            # Print only a portion of sensitive variables for confirmation
            print(f"INFO: docker_entrypoint.py:   {var_name}=<{var_value[:5]}...>")
        else:
            print(f"INFO: docker_entrypoint.py:   {var_name}={var_value}")
    sys.stdout.flush()
    # --- End Debug ---

    print("INFO: docker_entrypoint.py: Proceeding with database migrations...")
    sys.stdout.flush()
    if not execute_command(
        ['python', 'manage.py', 'migrate', '--noinput'],
        step_name="database migrations"
    ):
        print("ERROR: docker_entrypoint.py: Database migrations failed. Exiting.", file=sys.stderr)
        sys.exit(1) # Exit if migrations fail

    print("INFO: docker_entrypoint.py: Proceeding with superuser creation/verification...")
    sys.stdout.flush()
    execute_command(
        ['python', 'create_dev_admin.py'],
        step_name="superuser creation/verification",
        exit_on_error=False # Don't exit if superuser already exists or script has non-fatal issue
    )
    
    # Static files are collected during Docker build (RUN python manage.py collectstatic...)
    print("INFO: docker_entrypoint.py: Static files should have been collected during build.")
    sys.stdout.flush()

    # --- Prepare and Execute Gunicorn Command ---
    gunicorn_base_cmd_args = sys.argv[1:] # Get CMD from Dockerfile
    
    if not gunicorn_base_cmd_args:
        print("ERROR: docker_entrypoint.py: No Gunicorn command (CMD) provided from Dockerfile.", file=sys.stderr)
        sys.exit(1)

    # Get PORT from environment, default to 8000 if not set (Render WILL set $PORT)
    port = os.environ.get("PORT", "8000")
    
    # Substitute $PORT in the Gunicorn command arguments
    # Example CMD: ["gunicorn", "w1.wsgi:application", "--bind", "0.0.0.0:$PORT", ...]
    final_gunicorn_cmd_args = []
    for arg in gunicorn_base_cmd_args:
        final_gunicorn_cmd_args.append(arg.replace("$PORT", port))

    print(f"INFO: docker_entrypoint.py: Preparing to execute main Gunicorn command: {' '.join(final_gunicorn_cmd_args)}")
    sys.stdout.flush()
    
    try:
        # os.execvp replaces the current process (this script) with Gunicorn.
        # This is important for Gunicorn to be the main process and handle signals correctly.
        os.execvp(final_gunicorn_cmd_args[0], final_gunicorn_cmd_args)
    except FileNotFoundError:
        print(f"ERROR: docker_entrypoint.py: Gunicorn command '{final_gunicorn_cmd_args[0]}' not found. Ensure Gunicorn is installed in the Docker image.", file=sys.stderr)
        sys.exit(127)
    except Exception as e:
        print(f"ERROR: docker_entrypoint.py: Failed to execute Gunicorn command '{' '.join(final_gunicorn_cmd_args)}': {e}", file=sys.stderr)
        sys.exit(1)

    # This part should not be reached if os.execvp is successful
    print("ERROR: docker_entrypoint.py: os.execvp failed to replace the current process. This should not happen.", file=sys.stderr)
    sys.exit(1)