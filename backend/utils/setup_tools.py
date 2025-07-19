import os, subprocess
from pathlib import Path

def auto_setup():
    """ 自动完成环境配置 """
    # 安装依赖
    if not (Path("venv") / "bin").exists():
        subprocess.run(["python", "-m", "venv", "venv"], check=True)
    
    # 激活虚拟环境并安装依赖
    install_cmd = "source venv/bin/activate && pip install -r requirements.txt"
    subprocess.run(install_cmd, shell=True, executable="/bin/bash")

    # 复制环境变量模板
    if not Path(".env").exists():
        with open(".env.example") as src, open(".env", "w") as dst:
            dst.write(src.read())
    
    print("✅ 自动配置完成！请重启VS Code")

if __name__ == "__main__":
    auto_setup()
