import os
import pandas as pd
import random

from lib.mytube import download_subtitle, get_video_list
from lib.myai import get_summary

# === 設定頻道網址 ===
channel_url = 'https://www.youtube.com/@Drberg/videos'

# === 設定 CSV 檔案名稱 ===

base_dir = os.path.dirname(os.path.abspath(__file__)) + '/../'
script_dir = os.path.join(base_dir, 'scripts/')
summary_dir = os.path.join(base_dir, 'summary/')  
docs_dir = os.path.join(base_dir, 'docs/')
readme_file = os.path.join(base_dir, 'README.md')  
csv_file =  os.path.join(base_dir, 'src/video_list.csv')

def update_list():
    # === yt-dlp 參數設定 ===
    videos = get_video_list(channel_url)

    # === 建立新影片的DataFrame ===
    new_videos = []
    for video in reversed(videos):
        video_id = video.get('id')
        new_videos.append({
            'id': video_id,
            'title': video.get('title'),
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'date': video.get('upload_date', 'unknown')
        })

    new_df = pd.DataFrame(new_videos)

    # === 若日期存在，轉換格式 ===
    def format_date(date):
        return f"{date[:4]}-{date[4:6]}-{date[6:]}" if date != 'unknown' else date

    new_df['date'] = new_df['date'].apply(format_date)

    # === 讀取現有的CSV檔案 ===
    try:
        existing_df = pd.read_csv(csv_file)
        last_idx = existing_df['idx'].max()
    except FileNotFoundError:
        existing_df = pd.DataFrame(columns=['idx', 'id', 'title', 'url', 'date'])
        last_idx = 0

    # === 比較並合併新舊資料 ===
    new_videos_mask = ~new_df['id'].isin(existing_df['id'])
    if new_videos_mask.any():
        # 取得新影片並反轉順序
        new_videos_df = new_df[new_videos_mask].iloc[::-1].copy()
        # 為新影片加入遞增的 idx
        new_videos_count = len(new_videos_df)
        new_videos_df['idx'] = range(last_idx + 1, last_idx + new_videos_count + 1)
        
        # 合併新舊資料
        combined_df = pd.concat([existing_df, new_videos_df], ignore_index=True)
        
        # 儲存更新後的資料
        combined_df.to_csv(csv_file, index=False)
        print(f"📌 已更新 {new_videos_mask.sum()} 部新影片")
        return combined_df
    else:
        print("📌 沒有新影片")
        return existing_df

def download_script(df):
    # 確保 script_dir 存在
    os.makedirs(script_dir, exist_ok=True)
    
    # 讀取黑名單
    black_list_file = os.path.join(base_dir, 'src/black_list.csv')
    try:
        black_df = pd.read_csv(black_list_file)
    except FileNotFoundError:
        black_df = pd.DataFrame(columns=['idx', 'id', 'url'])
    
    # 計數器
    download_count = 0
    max_downloads = 10
    
    # 優先字幕語言列表
    preferred_langs = ['en']
    
    # 從最後一筆往前處理
    lst = df.index
    if random.random() < 0.5:
        lst = reversed(lst)
    for idx in lst:
        if download_count >= max_downloads:
            print(f"📌 已達到最大下載數量 ({max_downloads})")
            break
            
        video_id = df.loc[idx, 'id']
        
        # 檢查是否在黑名單中
        if video_id in black_df['id'].values:
            print(f"⚠️ 跳過黑名單影片：{idx}:{video_id}")
            continue
        
        script_file = f"{script_dir}/{video_id}.txt"
        
        # 檢查檔案是否已存在
        if os.path.exists(script_file):
            print(f"📌 跳過已存在的字幕：{idx}:{video_id}")
            continue
            
        print(f"📌 下載字幕中：{idx}:{video_id}")
        
        try:
            subtitle_text, formatted_date = download_subtitle(video_id, preferred_langs)

            # 存成字幕檔
            if subtitle_text:
                with open(script_file, 'w', encoding='utf-8') as f:
                    f.write(subtitle_text)
                print(f"✅ 字幕已儲存為：{script_file}") 
                download_count += 1
            
                # 更新 DataFrame 中的 upload_date
                if formatted_date:
                    df.loc[idx, 'date'] = formatted_date
                    # 更新 CSV 檔案
                    df.to_csv(csv_file, index=False)
                                                   
        except Exception as e:
            print(f"❌ 下載失敗 {idx}:{video_id}: {str(e)}")
            # 加入黑名單
            new_black = pd.DataFrame([{
                'idx': idx,
                'id': video_id,
                'url': f"https://www.youtube.com/watch?v={video_id}"
            }])
            black_df = pd.concat([black_df, new_black], ignore_index=True)
            # 儲存黑名單
            black_df.to_csv(black_list_file, index=False)
            print(f"⚠️ 已加入黑名單：{idx}:{video_id}")
            continue
   
    return df

def summerize_script():
    # 確保 summary 目錄存在
    os.makedirs(summary_dir, exist_ok=True)
    
    # 取得所有 scripts 目錄下的 txt 檔案
    script_files = [f for f in os.listdir(script_dir) if f.endswith('.txt')]
    
    # 計數器
    processed_count = 0
    
    for script_file in script_files:
        # 取得檔名（不含副檔名）
        fname = os.path.splitext(script_file)[0]
        
        # 檢查對應的 summary 檔案是否存在
        summary_file = f"{summary_dir}{fname}.md"
        script_path = f"{script_dir}{script_file}"
        
        if not os.path.exists(summary_file):
            print(f"📝 處理摘要中：{fname}")
            
            try:
                # 讀取字幕檔案
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 產生摘要
                summary_text = get_summary(content)
                
                # 寫入摘要檔案
                with open(summary_file, 'w', encoding='utf-8') as f:
                    f.write(summary_text)
                
                print(f"✅ 摘要已儲存：{summary_file}")
                processed_count += 1
                
            except Exception as e:
                print(f"❌ 摘要產生失敗 {fname}: {str(e)}")
                continue
    
    if processed_count > 0:
        print(f"📌 完成 {processed_count} 個檔案的摘要")
    else:
        print("📌 沒有需要處理的檔案")

def make_doc(filename: str, video_list: list):
    """
    將影片清單製作成文件
    Args:
        filename (str): 輸出的文件名稱
        video_list (list): 影片資料列表
    """

    # 檔案模板
    details_template = """<details>
<summary>{idx}. {date}{title}</summary><br>

<a href="https://www.youtube.com/watch?v={id}" target="_blank">
    <img src="https://img.youtube.com/vi/{id}/maxresdefault.jpg" 
        _target="blank" alt="[Youtube]" width="200">
</a>

{summary_file}
</details>

"""

    # 圖片模板
    image_template = """
"""

    try:
        # 確保目標目錄存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # 依 idx 由大到小排序
        sorted_videos = sorted(video_list, key=lambda x: x['idx'], reverse=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            for video in sorted_videos:
                # 處理日期格式
                id = video['id']
                date_str = f"[{video['date']}] " if video['date'] != 'unknown' else ""
                
                # 檢查是否有摘要檔案
                summary_path = f"{summary_dir}{id}.md"
                summary_content = ""
                if os.path.exists(summary_path):
                    with open(summary_path, 'r', encoding='utf-8') as sf:
                        summary_content = sf.read()
                
                # 填入模板
                content = details_template.format(
                    idx=video['idx'],
                    date=date_str,
                    title=video['title'],
                    id=id,
                    summary_file=summary_content
                )
                
                f.write(content)
                
    except Exception as e:
        print(f"❌ 製作文件失敗 {filename}: {str(e)}")

def create_readme_doc(max_idx, latest_date):
    content = f"""# Dr. Eric Berg DC ({latest_date})

---

"""
    # 反向計算範圍
    start_batch = (max_idx - 1) // 100  # 最大的批次編號
    
    # 從大到小遍歷
    for i in range(start_batch, -1, -1):
        start_idx = i * 100 + 1
        end_idx = min((i + 1) * 100, max_idx)
        content += f"- [{start_idx:04d}~{end_idx:04d}](docs/{i:02d}-index.md)\n"

    content += "\n---\n"

    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(content)


def create_doc(df):
    """
    從 DataFrame 中分批取出影片資料，並呼叫 make_doc 製作文件
    每批次處理 idx 範圍內的所有資料（如1-100內的所有存在的idx）
    檔名格式為 01-index.md, 02-index.md, ...
    """
    try:
        # 取得最大的 idx
        max_idx = df['idx'].max()
        batch_size = 100
        
        # 計算需要產生幾個檔案
        num_batches = (max_idx + batch_size - 1) // batch_size  # 向上取整
        
        # 處理每一批次
        for batch_num in range(num_batches):
            # 計算當前批次的 idx 範圍
            start_idx = batch_num * batch_size + 1
            end_idx = min((batch_num + 1) * batch_size, max_idx)
            
            # 取出符合 idx 範圍的資料
            batch_df = df[df['idx'].between(start_idx, end_idx)]
            
            # 如果這個範圍有資料才處理
            if not batch_df.empty:
                # 產生檔名 (01-index.md, 02-index.md, ...)
                filename = f"{docs_dir}/{batch_num:02d}-index.md"
                
                # 將 DataFrame 轉換成字典列表
                video_list = batch_df.to_dict('records')
                
                print(f"📝 處理文件：{filename} (idx: {start_idx}-{end_idx}, 實際筆數: {len(video_list)})")
                
                # 呼叫 make_doc 製作文件
                make_doc(filename, video_list)
                
                print(f"✅ 完成文件：{filename}")
        
        print(f"📌 總共產生了 {num_batches} 個文件")

        # 取得最新日期
        latest_date = df['date'].iloc[-1]
        create_readme_doc(max_idx, latest_date)
        
    except Exception as e:
        print(f"❌ 處理文件時發生錯誤：{str(e)}")

def email_notify():
    pass

if __name__ == '__main__':
    df = update_list()
    download_script(df)
    summerize_script()
    create_doc(df)
    email_notify()
