import os
import pandas as pd

from lib.mytube import download_subtitle, get_video_list
from lib.myai import get_summary

# === 設定頻道網址 ===
channel_url = 'https://www.youtube.com/@Drberg/videos'

# === 設定 CSV 檔案名稱 ===
csv_file = 'video_list.csv'

script_dir = os.path.dirname(os.path.abspath(__file__)) + '/../scripts/'
summary_dir = os.path.dirname(os.path.abspath(__file__)) + '/../summary/'

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
    
    # 計數器
    download_count = 0
    max_downloads = 3
    
    # 優先字幕語言列表
    preferred_langs = ['en']
    
    # 從最後一筆往前處理
    for idx in reversed(df.index):
        if download_count >= max_downloads:
            print(f"📌 已達到最大下載數量 ({max_downloads})")
            break
            
        video_id = df.loc[idx, 'id']
        script_file = f"{script_dir}/{video_id}.txt"
        
        # 檢查檔案是否已存在
        if os.path.exists(script_file):
            print(f"📌 跳過已存在的字幕：{video_id}")
            continue
            
        print(f"📌 下載字幕中：{video_id}")
        download_count += 1
        
        try:
            subtitle_text, formatted_date = download_subtitle(video_id, preferred_langs)

            # 存成字幕檔
            if subtitle_text:
                with open(script_file, 'w', encoding='utf-8') as f:
                    f.write(subtitle_text)
                print(f"✅ 字幕已儲存為：{script_file}") 
            
                # 更新 DataFrame 中的 upload_date
                if formatted_date:
                    df.loc[idx, 'date'] = formatted_date
                    # 更新 CSV 檔案
                    df.to_csv(csv_file, index=False)
                                                   
        except Exception as e:
            print(f"❌ 下載失敗 {video_id}: {str(e)}")
            continue

        summerize_script()
    
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

def create_doc():
    pass

def email_notify():
    pass

if __name__ == '__main__':
    df = update_list()
    download_script(df)
    # summerize_script()
    create_doc()
    email_notify()
