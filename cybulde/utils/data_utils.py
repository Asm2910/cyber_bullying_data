from pathlib import Path
from subprocess import CalledProcessError

from cybulde.utils.utils import get_logger, run_shell_command

DATA_UTILS_LOGGER = get_logger(Path(__file__).name)


def is_dvc_initialized() -> bool:
    return (Path().cwd() / ".dvc").exists()


def initialize_dvc() -> None:
    if is_dvc_initialized():
        DATA_UTILS_LOGGER.info("DVC is already initialized")
        return
    run_shell_command("dvc init")
    run_shell_command("dvc config core.analytics false")
    run_shell_command("dvc config core.autostage true")
    run_shell_command("git add .dvc")
    run_shell_command("git commit -nm 'Initialized DVC'")


def initialize_dvc_storage(dvc_remote_name: str, dvc_remote_url: str) -> None:
    if not run_shell_command("dvc remote list"):
        DATA_UTILS_LOGGER.info("Initializing DVC storage...")
        run_shell_command(f"dvc remote add -d {dvc_remote_name} {dvc_remote_url}")
        run_shell_command("git add .dvc/config")
        run_shell_command(f"git commit -nm 'Configured remote storage at: {dvc_remote_url}'")
    else:
        DATA_UTILS_LOGGER.info("DVC storage was already initialized...")


# --------------

# def commit_to_dvc(dvc_raw_data_folder: str, dvc_remote_name: str) -> None:
#     current_version = run_shell_command("git tag --list | sort -t v -k 2 -g | tail -1 | sed 's/v//'").strip()
#     if not current_version:
#         current_version = "0"
#     next_version = f"v{int(current_version) + 1}"
#     run_shell_command(f"dvc add {dvc_raw_data_folder}")
#     run_shell_command("git add .")
#     run_shell_command(f"git commit -m 'Updated version of data from v{current_version} to {next_version}'")
#     run_shell_command(f"git tag -a {next_version} -m 'Data version {next_version}'")
#     run_shell_command(f"dvc push {dvc_raw_data_folder}.dvc --remote {dvc_remote_name}")
#     run_shell_command("git push --follow-tags")
#     run_shell_command("git push -f --tags")

# -------------


def commit_to_dvc(dvc_raw_data_folder: str, dvc_remote_name: str) -> None:
    current_version = run_shell_command("git tag --list 'v*' | sort -t v -k 2 -g | tail -1 | sed 's/v//'").strip()
    if not current_version:
        current_version = "0"

    next_version = f"v{int(current_version) + 1}"

    # Track data via DVC (updates *.dvc + .gitignore if needed)
    run_shell_command(f"dvc add {dvc_raw_data_folder}")

    # Stage everything
    run_shell_command("git add -A")

    # ✅ If no changes -> do nothing (no crash)
    if not run_shell_command("git status --porcelain").strip():
        DATA_UTILS_LOGGER.info("No changes detected after `dvc add`. Skipping commit/tag/push.")
        return

    # Commit
    run_shell_command(f"git commit -m 'Updated version of data from v{current_version} to {next_version}'")

    # Tag only if tag doesn't already exist
    existing_tags = run_shell_command("git tag --list").split()
    if next_version not in existing_tags:
        run_shell_command(f"git tag -a {next_version} -m 'Data version {next_version}'")
    else:
        DATA_UTILS_LOGGER.info(f"Tag {next_version} already exists. Skipping tag creation.")

    # Push data to remote
    run_shell_command(f"dvc push {dvc_raw_data_folder}.dvc --remote {dvc_remote_name}")

    run_shell_command("git push --follow-tags")
    run_shell_command("git push -f --tags")


# def make_new_data_version(dvc_raw_data_folder: str, dvc_remote_name: str) -> None:
#     try:
#         status = run_shell_command(f"dvc status {dvc_raw_data_folder}.dvc")
#         if status == "Data and ppipelines are up to date.\n":
#             DATA_UTILS_LOGGER.info("Data and pipelines are upto date.")
#             return
#         commit_to_dvc(dvc_raw_data_folder, dvc_remote_name)
#     except CalledProcessError:
#         commit_to_dvc(dvc_raw_data_folder, dvc_remote_name)


def make_new_data_version(dvc_raw_data_folder: str, dvc_remote_name: str) -> None:
    try:
        status = run_shell_command(f"dvc status {dvc_raw_data_folder}.dvc").lower()
        if "up to date" in status:
            DATA_UTILS_LOGGER.info("Data and pipelines are up to date.")
            return
    except CalledProcessError as e:
        DATA_UTILS_LOGGER.warning(f"Could not read DVC status: {e}. Attempting version anyway.")

    commit_to_dvc(dvc_raw_data_folder, dvc_remote_name)
