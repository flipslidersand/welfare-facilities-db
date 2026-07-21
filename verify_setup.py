#!/usr/bin/env python3

"""
Welfare Facilities DB - Verification Script (Python version)
このスクリプトは、セットアップが正常に完了したかを確認します
"""

import subprocess
import requests
import sys
import os
from typing import Tuple, List

class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

class Verifier:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.checks: List[Tuple[str, bool]] = []
    
    def check_pass(self, message: str):
        print(f"{Colors.GREEN}✓ PASS{Colors.NC} {message}")
        self.passed += 1
        self.checks.append((message, True))
    
    def check_fail(self, message: str):
        print(f"{Colors.RED}✗ FAIL{Colors.NC} {message}")
        self.failed += 1
        self.checks.append((message, False))
    
    def check_warn(self, message: str):
        print(f"{Colors.YELLOW}⚠ WARN{Colors.NC} {message}")
        self.warnings += 1
    
    def run_command(self, cmd: str) -> Tuple[int, str, str]:
        """Run shell command and return (returncode, stdout, stderr)"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timeout"
        except Exception as e:
            return -1, "", str(e)
    
    def verify_docker_containers(self):
        """Check if all Docker containers are running"""
        print(f"\n{Colors.BLUE}1. Docker Containers{Colors.NC}")
        
        containers = {
            "welfare-db": "PostgreSQL",
            "welfare-api": "Backend API",
            "welfare-ui": "Frontend"
        }
        
        for container, name in containers.items():
            code, stdout, _ = self.run_command(f"docker-compose ps {container}")
            if code == 0 and "Up" in stdout:
                self.check_pass(f"{name} container ({container}) is running")
            else:
                self.check_fail(f"{name} container ({container}) is not running")
    
    def verify_ports(self):
        """Check if ports are accessible"""
        print(f"\n{Colors.BLUE}2. Port Availability{Colors.NC}")
        
        ports = [
            (8000, "Backend API"),
            (5173, "Frontend"),
            (5433, "PostgreSQL")
        ]
        
        for port, name in ports:
            try:
                response = requests.get(f"http://localhost:{port}", timeout=2)
                self.check_pass(f"Port {port} ({name}) is accessible")
            except:
                self.check_warn(f"Port {port} ({name}) is not accessible")
    
    def verify_health_checks(self):
        """Check service health"""
        print(f"\n{Colors.BLUE}3. Health Checks{Colors.NC}")
        
        # Backend API health check
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200 and "healthy" in response.text:
                self.check_pass("Backend API health check")
            else:
                self.check_fail("Backend API health check failed")
        except:
            self.check_fail("Backend API health check - connection failed")
        
        # PostgreSQL health check
        code, _, _ = self.run_command("docker-compose exec -T db pg_isready -U dev")
        if code == 0:
            self.check_pass("PostgreSQL is ready")
        else:
            self.check_fail("PostgreSQL is not ready")
    
    def verify_api_endpoints(self):
        """Check key API endpoints"""
        print(f"\n{Colors.BLUE}4. API Endpoints{Colors.NC}")
        
        endpoints = [
            ("/api/corporations", "Corporations list"),
            ("/health", "Health check"),
            ("/docs", "API documentation")
        ]
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                if response.status_code in [200, 307, 308]:
                    self.check_pass(f"GET {endpoint} ({name})")
                else:
                    self.check_warn(f"GET {endpoint} returned {response.status_code}")
            except requests.ConnectionError:
                self.check_fail(f"GET {endpoint} - connection failed")
            except:
                self.check_warn(f"GET {endpoint} - request failed")
    
    def verify_configuration(self):
        """Check configuration files"""
        print(f"\n{Colors.BLUE}5. Environment Configuration{Colors.NC}")
        
        if os.path.exists("backend/.env"):
            self.check_pass("backend/.env file exists")
            
            with open("backend/.env", "r") as f:
                content = f.read()
                if "DATABASE_URL" in content:
                    self.check_pass("DATABASE_URL is configured")
                else:
                    self.check_fail("DATABASE_URL is not configured")
        else:
            self.check_fail("backend/.env file not found")
    
    def verify_volumes(self):
        """Check Docker volumes"""
        print(f"\n{Colors.BLUE}6. Docker Volumes{Colors.NC}")
        
        code, stdout, _ = self.run_command("docker volume ls")
        if "pgdata" in stdout:
            self.check_pass("PostgreSQL volume (pgdata) exists")
        else:
            self.check_warn("PostgreSQL volume (pgdata) not found")
    
    def print_summary(self):
        """Print summary and exit with appropriate code"""
        print(f"\n{Colors.BLUE}=== Summary ==={Colors.NC}")
        print(f"{Colors.GREEN}PASSED:  {self.passed}{Colors.NC}")
        if self.failed > 0:
            print(f"{Colors.RED}FAILED:  {self.failed}{Colors.NC}")
        if self.warnings > 0:
            print(f"{Colors.YELLOW}WARNINGS: {self.warnings}{Colors.NC}")
        
        print("")
        
        if self.failed == 0:
            print(f"{Colors.GREEN}✓ Setup verification completed successfully!{Colors.NC}")
            print("")
            print("Service URLs:")
            print("  Frontend:   http://localhost:5173")
            print("  Backend:    http://localhost:8000")
            print("  API Docs:   http://localhost:8000/docs")
            return 0
        else:
            print(f"{Colors.RED}✗ Setup verification found issues. See above for details.{Colors.NC}")
            return 1
    
    def run(self):
        """Run all verification checks"""
        print(f"{Colors.BLUE}=== Welfare Facilities DB - Setup Verification ==={Colors.NC}")
        
        self.verify_docker_containers()
        self.verify_ports()
        self.verify_health_checks()
        self.verify_api_endpoints()
        self.verify_configuration()
        self.verify_volumes()
        
        exit_code = self.print_summary()
        sys.exit(exit_code)

if __name__ == "__main__":
    verifier = Verifier()
    verifier.run()
