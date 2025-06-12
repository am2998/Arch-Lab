#!/usr/bin/env python3
# ZFS Assistant - Privilege Management System
# Author: GitHub Copilot

import subprocess
import tempfile
import os
import time
from typing import List, Tuple, Optional
from .logger import log_info, log_error, log_warning, log_success


class PrivilegeManager:    """Manages elevated privileges for ZFS operations with minimal user prompts."""
    
    def __init__(self):
        self._auth_cache_time = 0
        self._auth_cache_duration = 300  # 5 minutes
        self._session_active = False
    
    def _is_auth_cached(self) -> bool:
        """Check if we have recent authentication cache."""
        return (time.time() - self._auth_cache_time) < self._auth_cache_duration
      def _refresh_auth_cache(self) -> bool:
        """Refresh authentication cache."""
        try:
            result = subprocess.run(['pkexec', 'true'], 
                                  check=True, capture_output=True, timeout=30)
            self._auth_cache_time = time.time()
            self._session_active = True
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            self._session_active = False
            return False
      def run_privileged_command(self, command: List[str]) -> Tuple[bool, str]:
        """
        Run a single privileged command.
        
        Args:
            command: Command to run as list of strings
            
        Returns:
            (success, output_or_error) tuple
        """
        try:
            # Refresh auth cache if needed
            if not self._is_auth_cached():
                if not self._refresh_auth_cache():
                    return False, "Failed to obtain administrative privileges"
            
            # Run the actual command
            full_command = ['pkexec'] + command
            log_info(f"Running privileged command: {' '.join(command)}")
            
            result = subprocess.run(full_command, 
                                  check=True, capture_output=True, text=True, timeout=60)
            
            log_success(f"Command completed successfully: {' '.join(command)}")
            return True, result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {e.stderr.strip() if e.stderr else str(e)}"
            log_error(f"Privileged command failed: {' '.join(command)}", {
                'error': error_msg,
                'return_code': e.returncode
            })
            return False, error_msg
        except subprocess.TimeoutExpired:
            error_msg = "Command timed out"
            log_error(f"Privileged command timed out: {' '.join(command)}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            log_error(f"Unexpected error in privileged command: {' '.join(command)}", {
                'error': error_msg
            })
            return False, error_msg
    
    def run_batch_privileged_commands(self, commands: List[List[str]]) -> Tuple[bool, str]:
        """
        Run multiple privileged commands in a single pkexec session using a bash script.
        This significantly reduces the number of pkexec prompts.
        
        Args:
            commands: List of commands, each command is a list of strings
            
        Returns:
            (success, output_or_error) tuple
        """
        if not commands:
            return True, "No commands to execute"
        
        try:
            # Refresh auth cache if needed
            if not self._is_auth_cached():
                if not self._refresh_auth_cache():
                    return False, "Failed to obtain administrative privileges"
            
            # Create a temporary bash script
            script_lines = [
                "#!/bin/bash",
                "set -e  # Exit on any error",
                ""
            ]
            
            # Add each command to the script
            for command in commands:
                # Escape single quotes in command arguments
                escaped_command = []
                for arg in command:
                    if "'" in arg:
                        escaped_arg = arg.replace("'", "'\"'\"'")
                        escaped_command.append(f"'{escaped_arg}'")
                    else:
                        escaped_command.append(f"'{arg}'")
                
                script_lines.append(f"echo 'Executing: {' '.join(command)}'")
                script_lines.append(f"{' '.join(escaped_command)}")
                script_lines.append("")
            
            script_content = '\n'.join(script_lines)
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
                temp_file.write(script_content)
                temp_script_path = temp_file.name
            
            try:
                # Make script executable
                os.chmod(temp_script_path, 0o755)
                
                # Execute the batch script with pkexec
                log_info(f"Running batch of {len(commands)} privileged commands")
                
                result = subprocess.run(['pkexec', 'bash', temp_script_path], 
                                      check=True, capture_output=True, text=True, timeout=300)
                
                log_success(f"Batch execution completed successfully ({len(commands)} commands)")
                return True, result.stdout.strip()
                
            finally:
                # Clean up temporary script
                try:
                    os.unlink(temp_script_path)
                except:
                    pass
                    
        except subprocess.CalledProcessError as e:
            error_msg = f"Batch execution failed: {e.stderr.strip() if e.stderr else str(e)}"
            log_error("Batch privileged command execution failed", {
                'error': error_msg,
                'return_code': e.returncode,
                'command_count': len(commands)
            })
            return False, error_msg
        except subprocess.TimeoutExpired:
            error_msg = "Batch execution timed out"
            log_error("Batch privileged command execution timed out", {
                'command_count': len(commands)
            })
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error in batch execution: {str(e)}"
            log_error("Unexpected error in batch privileged command execution", {
                'error': error_msg,
                'command_count': len(commands)
            })
            return False, error_msg
    
    def copy_files_privileged(self, file_operations: List[Tuple[str, str]]) -> Tuple[bool, str]:
        """
        Copy multiple files with elevated privileges in a single pkexec session.
        
        Args:
            file_operations: List of (source_path, destination_path) tuples
            
        Returns:
            (success, output_or_error) tuple
        """
        if not file_operations:
            return True, "No files to copy"
        
        commands = []
        for src, dst in file_operations:
            # Create destination directory if needed
            dst_dir = os.path.dirname(dst)
            if dst_dir:
                commands.append(['mkdir', '-p', dst_dir])
            commands.append(['cp', src, dst])
        
        return self.run_batch_privileged_commands(commands)
    
    def remove_files_privileged(self, file_paths: List[str]) -> Tuple[bool, str]:
        """
        Remove multiple files with elevated privileges in a single pkexec session.
        
        Args:
            file_paths: List of file paths to remove
            
        Returns:
            (success, output_or_error) tuple
        """
        if not file_paths:
            return True, "No files to remove"
        
        commands = [['rm', '-f'] + file_paths]
        return self.run_batch_privileged_commands(commands)
    
    def create_script_privileged(self, script_path: str, script_content: str, 
                                executable: bool = True) -> Tuple[bool, str]:
        """
        Create a script file with elevated privileges.
        
        Args:
            script_path: Path where to create the script
            script_content: Content of the script
            executable: Whether to make the script executable
            
        Returns:
            (success, output_or_error) tuple
        """
        try:
            # Create temporary file first
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp') as temp_file:
                temp_file.write(script_content)
                temp_path = temp_file.name
            
            try:
                commands = [
                    ['mkdir', '-p', os.path.dirname(script_path)],
                    ['cp', temp_path, script_path]
                ]
                
                if executable:
                    commands.append(['chmod', '755', script_path])
                
                return self.run_batch_privileged_commands(commands)
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            error_msg = f"Error creating script with elevated privileges: {str(e)}"
            log_error("Failed to create script with elevated privileges", {
                'script_path': script_path,
                'error': error_msg
            })
            return False, error_msg
    
    def cleanup_session(self):
        """Clean up the privilege session."""
        self._session_active = False
        self._auth_cache_time = 0


# Global instance for easy access
privilege_manager = PrivilegeManager()
