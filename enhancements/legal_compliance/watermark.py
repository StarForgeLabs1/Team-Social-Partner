from datetime import datetime

def embed_watermark(content: str, user_id: str) -> str:
    """ 与原仓库的Post.create方法兼容 """
    return f"{content}\nⓒ{datetime.now().year}-{user_id[:4]}"
