#!/bin/bash

# Warif Security Hardening Script
# This script implements security best practices for production deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Security hardening functions
harden_docker() {
    log_info "Hardening Docker configuration..."
    
    # Create Docker daemon configuration
    sudo mkdir -p /etc/docker
    sudo tee /etc/docker/daemon.json > /dev/null << EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "live-restore": true,
    "userland-proxy": false,
    "no-new-privileges": true,
    "seccomp-profile": "/etc/docker/seccomp-profile.json",
    "apparmor-profile": "docker-default"
}
EOF

    # Create seccomp profile
    sudo tee /etc/docker/seccomp-profile.json > /dev/null << EOF
{
    "defaultAction": "SCMP_ACT_ERRNO",
    "architectures": [
        "SCMP_ARCH_X86_64",
        "SCMP_ARCH_X86",
        "SCMP_ARCH_X32"
    ],
    "syscalls": [
        {
            "names": [
                "accept",
                "accept4",
                "access",
                "alarm",
                "bind",
                "brk",
                "capget",
                "capset",
                "chdir",
                "chmod",
                "chown",
                "chroot",
                "clock_getres",
                "clock_gettime",
                "clock_nanosleep",
                "close",
                "connect",
                "copy_file_range",
                "creat",
                "dup",
                "dup2",
                "dup3",
                "epoll_create",
                "epoll_create1",
                "epoll_ctl",
                "epoll_pwait",
                "epoll_wait",
                "eventfd",
                "eventfd2",
                "execve",
                "execveat",
                "exit",
                "exit_group",
                "faccessat",
                "fadvise64",
                "fallocate",
                "fanotify_mark",
                "fchdir",
                "fchmod",
                "fchmodat",
                "fchown",
                "fchownat",
                "fcntl",
                "fdatasync",
                "fgetxattr",
                "flistxattr",
                "flock",
                "fork",
                "fremovexattr",
                "fsetxattr",
                "fstat",
                "fstatfs",
                "fsync",
                "ftruncate",
                "futex",
                "getcwd",
                "getdents",
                "getdents64",
                "getegid",
                "geteuid",
                "getgid",
                "getgroups",
                "getpeername",
                "getpgid",
                "getpgrp",
                "getpid",
                "getppid",
                "getpriority",
                "getrandom",
                "getresgid",
                "getresuid",
                "getrlimit",
                "get_robust_list",
                "getrusage",
                "getsid",
                "getsockname",
                "getsockopt",
                "get_thread_area",
                "gettid",
                "gettimeofday",
                "getuid",
                "getxattr",
                "inotify_add_watch",
                "inotify_init",
                "inotify_init1",
                "inotify_rm_watch",
                "io_cancel",
                "ioctl",
                "io_destroy",
                "io_getevents",
                "ioprio_get",
                "ioprio_set",
                "io_setup",
                "io_submit",
                "ipc",
                "kill",
                "lchown",
                "lgetxattr",
                "link",
                "linkat",
                "listen",
                "listxattr",
                "llistxattr",
                "lremovexattr",
                "lseek",
                "lsetxattr",
                "lstat",
                "madvise",
                "mincore",
                "mkdir",
                "mkdirat",
                "mknod",
                "mknodat",
                "mlock",
                "mlockall",
                "mmap",
                "mmap2",
                "mprotect",
                "mq_getsetattr",
                "mq_notify",
                "mq_open",
                "mq_timedreceive",
                "mq_timedsend",
                "mq_unlink",
                "mremap",
                "msgctl",
                "msgget",
                "msgrcv",
                "msgsnd",
                "msync",
                "munlock",
                "munlockall",
                "munmap",
                "nanosleep",
                "newfstatat",
                "_newselect",
                "open",
                "openat",
                "pause",
                "pipe",
                "pipe2",
                "poll",
                "ppoll",
                "prctl",
                "pread64",
                "preadv",
                "prlimit64",
                "pselect6",
                "ptrace",
                "pwrite64",
                "pwritev",
                "read",
                "readahead",
                "readlink",
                "readlinkat",
                "readv",
                "recv",
                "recvfrom",
                "recvmmsg",
                "recvmsg",
                "remap_file_pages",
                "removexattr",
                "rename",
                "renameat",
                "renameat2",
                "restart_syscall",
                "rmdir",
                "rt_sigaction",
                "rt_sigpending",
                "rt_sigprocmask",
                "rt_sigqueueinfo",
                "rt_sigreturn",
                "rt_sigsuspend",
                "rt_sigtimedwait",
                "rt_tgsigqueueinfo",
                "sched_get_priority_max",
                "sched_get_priority_min",
                "sched_getaffinity",
                "sched_getparam",
                "sched_getscheduler",
                "sched_rr_get_interval",
                "sched_setaffinity",
                "sched_setparam",
                "sched_setscheduler",
                "sched_yield",
                "seccomp",
                "select",
                "send",
                "sendfile",
                "sendmmsg",
                "sendmsg",
                "sendto",
                "setfsgid",
                "setfsuid",
                "setgid",
                "setgroups",
                "setitimer",
                "setpgid",
                "setpriority",
                "setregid",
                "setresgid",
                "setresuid",
                "setreuid",
                "setrlimit",
                "set_robust_list",
                "setsid",
                "setsockopt",
                "set_thread_area",
                "set_tid_address",
                "setuid",
                "setxattr",
                "shmat",
                "shmctl",
                "shmdt",
                "shmget",
                "shutdown",
                "sigaltstack",
                "signalfd",
                "signalfd4",
                "sigreturn",
                "socket",
                "socketcall",
                "socketpair",
                "splice",
                "stat",
                "statfs",
                "symlink",
                "symlinkat",
                "sync",
                "sync_file_range",
                "syncfs",
                "sysinfo",
                "syslog",
                "tee",
                "tgkill",
                "time",
                "timer_create",
                "timer_delete",
                "timer_getoverrun",
                "timer_gettime",
                "timer_settime",
                "timerfd_create",
                "timerfd_gettime",
                "timerfd_settime",
                "times",
                "tkill",
                "truncate",
                "umask",
                "uname",
                "unlink",
                "unlinkat",
                "utime",
                "utimensat",
                "utimes",
                "vfork",
                "vmsplice",
                "wait4",
                "waitid",
                "waitpid",
                "write",
                "writev"
            ],
            "action": "SCMP_ACT_ALLOW"
        }
    ]
}
EOF

    # Restart Docker daemon
    sudo systemctl restart docker
    
    log_success "Docker hardening completed"
}

harden_firewall() {
    log_info "Configuring firewall..."
    
    # Install UFW if not present
    if ! command -v ufw &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y ufw
    fi
    
    # Reset UFW to defaults
    sudo ufw --force reset
    
    # Set default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Allow Warif ports
    sudo ufw allow 8010/tcp  # API
    sudo ufw allow 8501/tcp  # Dashboard
    sudo ufw allow 9090/tcp  # Prometheus
    sudo ufw allow 3000/tcp  # Grafana
    sudo ufw allow 8080/tcp  # Traefik Dashboard
    
    # Allow MQTT ports
    sudo ufw allow 1883/tcp  # MQTT
    sudo ufw allow 8883/tcp  # MQTT over TLS
    sudo ufw allow 9001/tcp  # MQTT WebSocket
    
    # Enable UFW
    sudo ufw --force enable
    
    log_success "Firewall configured"
}

harden_ssl() {
    log_info "Hardening SSL/TLS configuration..."
    
    # Create SSL configuration for Traefik
    sudo mkdir -p /etc/ssl/green-engine
    sudo tee /etc/ssl/green-engine/ssl.conf > /dev/null << EOF
# SSL Configuration for Warif

# Disable weak protocols
SSLProtocol -all +TLSv1.2 +TLSv1.3

# Disable weak ciphers
SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384

# Enable HSTS
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"

# Enable security headers
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'"

# Disable server signature
ServerTokens Prod
ServerSignature Off
EOF

    log_success "SSL/TLS hardening completed"
}

harden_database() {
    log_info "Hardening database configuration..."
    
    # Create PostgreSQL security configuration
    sudo tee /etc/postgresql/security.conf > /dev/null << EOF
# PostgreSQL Security Configuration

# Connection settings
listen_addresses = 'localhost'
port = 5432
max_connections = 100

# Authentication
password_encryption = scram-sha-256
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
ssl_ca_file = 'ca.crt'

# Logging
log_connections = on
log_disconnections = on
log_statement = 'all'
log_min_duration_statement = 1000

# Security
shared_preload_libraries = 'pg_stat_statements'
track_activities = on
track_counts = on
track_io_timing = on
track_functions = all

# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
checkpoint_timeout = 5min
max_wal_size = 1GB
min_wal_size = 80MB
EOF

    log_success "Database hardening completed"
}

harden_logging() {
    log_info "Setting up centralized logging..."
    
    # Create logrotate configuration
    sudo tee /etc/logrotate.d/green-engine > /dev/null << EOF
/var/log/green-engine/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        /bin/kill -HUP \`cat /var/run/rsyslogd.pid 2> /dev/null\` 2> /dev/null || true
    endscript
}
EOF

    # Create log directory
    sudo mkdir -p /var/log/green-engine
    sudo chown root:root /var/log/green-engine
    sudo chmod 755 /var/log/green-engine

    log_success "Logging configuration completed"
}

harden_monitoring() {
    log_info "Setting up security monitoring..."
    
    # Create fail2ban configuration
    sudo tee /etc/fail2ban/jail.d/green-engine.conf > /dev/null << EOF
[green-engine-api]
enabled = true
port = 8010
filter = green-engine-api
logpath = /var/log/green-engine/api.log
maxretry = 5
bantime = 3600
findtime = 600

[green-engine-dashboard]
enabled = true
port = 8501
filter = green-engine-dashboard
logpath = /var/log/green-engine/dashboard.log
maxretry = 5
bantime = 3600
findtime = 600
EOF

    # Create fail2ban filters
    sudo tee /etc/fail2ban/filter.d/green-engine-api.conf > /dev/null << EOF
[Definition]
failregex = ^.*\"POST /api/v1/.*\" 4[0-9][0-9] .*$
            ^.*\"GET /api/v1/.*\" 4[0-9][0-9] .*$
ignoreregex =
EOF

    sudo tee /etc/fail2ban/filter.d/green-engine-dashboard.conf > /dev/null << EOF
[Definition]
failregex = ^.*\"GET /.*\" 4[0-9][0-9] .*$
ignoreregex =
EOF

    # Start fail2ban
    sudo systemctl enable fail2ban
    sudo systemctl start fail2ban

    log_success "Security monitoring configured"
}

harden_system() {
    log_info "Hardening system configuration..."
    
    # Update system packages
    sudo apt-get update && sudo apt-get upgrade -y
    
    # Install security tools
    sudo apt-get install -y fail2ban ufw unattended-upgrades
    
    # Configure automatic security updates
    sudo tee /etc/apt/apt.conf.d/50unattended-upgrades > /dev/null << EOF
Unattended-Upgrade::Allowed-Origins {
    "\${distro_id}:\${distro_codename}-security";
    "\${distro_id}ESMApps:\${distro_codename}-apps-security";
    "\${distro_id}ESM:\${distro_codename}-infra-security";
};

Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

    # Enable automatic updates
    sudo tee /etc/apt/apt.conf.d/20auto-upgrades > /dev/null << EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF

    # Configure kernel parameters for security
    sudo tee /etc/sysctl.d/99-green-engine-security.conf > /dev/null << EOF
# Network security
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_rfc1337 = 1

# Memory protection
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1

# File system protection
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
EOF

    # Apply sysctl settings
    sudo sysctl -p /etc/sysctl.d/99-green-engine-security.conf

    log_success "System hardening completed"
}

create_security_script() {
    log_info "Creating security maintenance script..."
    
    sudo tee /usr/local/bin/green-engine-security.sh > /dev/null << 'EOF'
#!/bin/bash

# Warif Security Maintenance Script

# Check for security updates
echo "Checking for security updates..."
apt list --upgradable | grep -i security

# Check fail2ban status
echo "Checking fail2ban status..."
fail2ban-client status

# Check firewall status
echo "Checking firewall status..."
ufw status

# Check Docker security
echo "Checking Docker security..."
docker version
docker info | grep -i security

# Check SSL certificates
echo "Checking SSL certificates..."
find /etc/ssl -name "*.crt" -exec openssl x509 -in {} -text -noout \; | grep -E "(Not After|Subject:)"

# Check log files for suspicious activity
echo "Checking for suspicious activity..."
grep -i "failed\|error\|denied" /var/log/green-engine/*.log | tail -20

echo "Security check completed."
EOF

    sudo chmod +x /usr/local/bin/green-engine-security.sh

    log_success "Security maintenance script created"
}

# Main function
main() {
    log_info "Starting Warif security hardening..."
    
    harden_system
    harden_docker
    harden_firewall
    harden_ssl
    harden_database
    harden_logging
    harden_monitoring
    create_security_script
    
    log_success "Security hardening completed!"
    echo
    echo "🔒 Security hardening summary:"
    echo "  • Docker daemon secured with seccomp and AppArmor"
    echo "  • Firewall configured with UFW"
    echo "  • SSL/TLS hardened with strong ciphers"
    echo "  • Database secured with encryption and logging"
    echo "  • Centralized logging configured"
    echo "  • Security monitoring with fail2ban"
    echo "  • System hardened with kernel parameters"
    echo "  • Security maintenance script created"
    echo
    echo "📋 Next steps:"
    echo "  1. Review and update firewall rules as needed"
    echo "  2. Configure SSL certificates for production"
    echo "  3. Set up log monitoring and alerting"
    echo "  4. Regular security audits with /usr/local/bin/green-engine-security.sh"
    echo "  5. Keep system and Docker images updated"
}

# Run main function
main "$@"
