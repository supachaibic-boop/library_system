import subprocess
import datetime
import os

# Configuration
OUTPUT_FILE = "/var/www/html/status.html"
HOSTNAME = "OpenClaw-Server"

def get_command_output(cmd):
    try:
        return subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
    except Exception as e:
        return f"Error: {e}"

def generate_html():
    # Gather Data
    uptime = get_command_output("uptime -p")
    cpu_load = get_command_output("cat /proc/loadavg | cut -d' ' -f1")
    mem_info = get_command_output("free -h")
    disk_info = get_command_output("df -h / | tail -1")
    top_processes = get_command_output("ps aux --sort=-%cpu | head -n 11")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Memory data parsing
    mem_lines = mem_info.split('\n')
    mem_data = mem_lines[1].split() if len(mem_lines) > 1 else ["N/A"]*4
    total_mem = mem_data[1]
    used_mem = mem_data[2]
    free_mem = mem_data[3]

    # Disk data parsing
    disk_data = disk_info.split()
    disk_total = disk_data[1]
    disk_used_pct = disk_data[4]

    html_content = f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>nmon-style Status - {HOSTNAME}</title>
        <style>
            body {{ 
                background-color: #000; 
                color: #00FF00; 
                font-family: 'Courier New', Courier, monospace; 
                padding: 20px;
                line-height: 1.2;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                border: 2px solid #00FF00;
                padding: 15px;
            }}
            .header {{
                text-align: center;
                font-weight: bold;
                font-size: 1.5rem;
                margin-bottom: 20px;
                border-bottom: 2px solid #00FF00;
                padding-bottom: 10px;
                text-transform: uppercase;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }}
            .section {{
                border: 1px solid #00FF00;
                padding: 10px;
                position: relative;
            }}
            .section-title {{
                position: absolute;
                top: -12px;
                left: 10px;
                background-color: #000;
                padding: 0 5px;
                font-weight: bold;
                color: #FFF;
            }}
            .data-row {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
            }}
            .label {{ color: #AAA; }}
            .value {{ color: #00FF00; font-weight: bold; }}
            pre {{
                background-color: #000;
                color: #00FF00;
                font-family: 'Courier New', Courier, monospace;
                font-size: 12px;
                overflow-x: auto;
                margin-top: 10px;
                border: 1px solid #00FF00;
                padding: 10px;
            }}
            .footer {{
                margin-top: 20px;
                text-align: right;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                {HOSTNAME} SYSTEM MONITOR (NMON MODE)
            </div>

            <div class="grid">
                <div class="section">
                    <div class="section-title">CPU & SYSTEM</div>
                    <div class="data-row">
                        <span class="label">Uptime:</span>
                        <span class="value">{uptime}</span>
                    </div>
                    <div class="data-row">
                        <span class="label">Load Avg (1m):</span>
                        <span class="value">{cpu_load}</span>
                    </div>
                    <div class="data-row">
                        <span class="label">Status:</span>
                        <span class="value">RUNNING</span>
                    </div>
                </div>

                <div class="section">
                    <div class="section-title">MEMORY</div>
                    <div class="data-row">
                        <span class="label">Total:</span>
                        <span class="value">{total_mem}</span>
                    </div>
                    <div class="data-row">
                        <span class="label">Used:</span>
                        <span class="value">{used_mem}</span>
                    </div>
                    <div class="data-row">
                        <span class="label">Free:</span>
                        <span class="value">{free_mem}</span>
                    </div>
                </div>
            </div>

            <div class="section" style="margin-top: 20px;">
                <div class="section-title">DISK /ROOT</div>
                <div class="data-row">
                    <span class="label">Total Space:</span>
                    <span class="value">{disk_total}</span>
                    <span class="label">Used %:</span>
                    <span class="value">{disk_used_pct}</span>
                </div>
            </div>

            <div class="section" style="margin-top: 20px;">
                <div class="section-title">TOP PROCESSES (CPU%)</div>
                <pre>{top_processes}</pre>
            </div>

            <div class="footer">
                Last Update: {timestamp} | Managed by OpenClaw Agent "Kung" 📈
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    generate_html()
