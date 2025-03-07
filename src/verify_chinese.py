import os
import glob
import re

def detect_chinese(text):
    # 計算中文字元數量
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    num_chinese = len(chinese_chars)
    total_chars = len(text)

    return num_chinese / total_chars if total_chars > 0 else 0

def verify_summaries():
    """
    檢查 summary 目錄下所有 .md 檔案的中文內容
    印出中文比例低於閾值的檔案名稱和內容
    讓使用者確認是否刪除
    """
    # 設定目錄和閾值
    summary_dir = os.path.dirname(os.path.abspath(__file__)) + '/../summary/'
    threshold = 0.3

    # 取得所有 .md 檔案
    md_files = glob.glob(os.path.join(summary_dir, "*.md"))
    
    print(f"📝 開始檢查 {len(md_files)} 個檔案")
    
    # 檢查每個檔案
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢測中文比例
            chinese_ratio = detect_chinese(content)
            
            # 如果比例低於閾值，印出檔案資訊並詢問是否刪除
            if chinese_ratio < threshold:
                filename = os.path.basename(md_file)
                print(f"\n❌ 檔案中文比例過低 ({chinese_ratio:.2f}): {filename}")
                # print("=== 檔案內容 ===")
                # print(content)
                # print("===============")
                os.remove(md_file)
                print(f"✅ 已刪除：{filename}")
        
        except Exception as e:
            print(f"❌ 處理檔案時發生錯誤 {md_file}: {str(e)}")
    
    print("\n📌 檢查完成")

if __name__ == '__main__':
    verify_summaries()
