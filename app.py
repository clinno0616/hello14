import streamlit as st
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError
import json
import pandas as pd
import math
import io

class ElasticsearchClient:
    def __init__(self, host='192.168.x.x', port=9200, scheme='http'):
        """初始化 Elasticsearch 客戶端"""
        self.client = None
        try:
            # ES 6.8.2 的連接配置
            self.client = Elasticsearch(
                hosts=[{'host': host, 'port': port, 'scheme': scheme}],
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            if not self.client.ping():
                raise ConnectionError("無法連接到 Elasticsearch")
                
        except ConnectionError as e:
            st.error(f"連接失敗，請檢查 Elasticsearch 是否正在運行於 {scheme}://{host}:{port}")
            raise e

    def list_indices(self):
        """列出所有索引"""
        try:
            # 使用 ES 6.x 的方式獲取索引
            indices = self.client.indices.get_alias("*")
            return sorted(list(indices.keys()), reverse=True)
        except Exception as e:
            st.error(f"獲取索引列表時發生錯誤: {str(e)}")
            return []

    def get_mapping_info(self, index_name):
        """獲取索引的映射信息"""
        try:
            mapping = self.client.indices.get_mapping(index=index_name)
            if index_name in mapping:
                # ES 6.x 的映射結構
                mappings = mapping[index_name]['mappings']
                # 獲取第一個可用的類型
                doc_type = next(iter(mappings.keys()))
                return doc_type, mappings[doc_type]
            return '_doc', None
        except Exception as e:
            st.error(f"獲取映射信息時發生錯誤: {str(e)}")
            return '_doc', None

    def get_index_stats(self, index_name):
        """獲取索引統計資訊"""
        try:
            stats = self.client.indices.stats(index=index_name)
            return {
                "文檔數量": stats['indices'][index_name]['total']['docs']['count'],
                "已刪除文檔": stats['indices'][index_name]['total']['docs']['deleted'],
                "存儲大小(bytes)": stats['indices'][index_name]['total']['store']['size_in_bytes'],
                "索引操作次數": stats['indices'][index_name]['total']['indexing']['index_total'],
                "搜尋操作次數": stats['indices'][index_name]['total']['search']['query_total']
            }
        except Exception as e:
            st.error(f"獲取索引統計資訊時發生錯誤: {str(e)}")
            return None

    def search_documents(self, index_name, size=100):
        """搜尋文檔"""
        try:
            # 獲取文檔類型
            doc_type, mapping = self.get_mapping_info(index_name)
            
            # ES 6.x 的查詢結構
            query_body = {
                "size": size,
                "query": {
                    "match_all": {}
                },
                "sort": [
                    {"_id": "asc"}
                ]
            }

            # 使用 ES 6.x 的搜尋 API
            response = self.client.search(
                index=index_name,
                doc_type=doc_type,
                body=query_body,
                request_timeout=30
            )

            # 調試信息
            total_hits = response['hits']['total']
            if isinstance(total_hits, dict):  # ES 7.x 格式
                total_count = total_hits['value']
            else:  # ES 6.x 格式
                total_count = total_hits
            
            st.write(f"找到 {total_count} 條記錄")

            # 解析搜尋結果
            documents = []
            for hit in response['hits']['hits']:
                doc = {}
                # 添加文檔源數據
                if '_source' in hit:
                    doc.update(hit['_source'])
                # 添加元數據
                doc['_id'] = hit['_id']
                doc['_type'] = hit['_type']
                doc['_index'] = hit['_index']
                documents.append(doc)

            return documents

        except Exception as e:
            st.error(f"搜尋文檔時發生錯誤: {str(e)}")
            import traceback
            st.write("詳細錯誤信息：", traceback.format_exc())
            return []

def display_paginated_dataframe(df, page_size, show_debug=False):
    """顯示分頁的 DataFrame"""
    # 計算總頁數
    total_rows = len(df)
    total_pages = math.ceil(total_rows / page_size)
    
    # 如果 session state 中沒有當前頁碼，初始化為1
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    # 創建分頁控制按鈕的容器
    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 3])
    
    # 第一頁按鈕
    with col1:
        if st.button("⏮️ 第一頁", disabled=st.session_state.current_page == 1):
            st.session_state.current_page = 1
            st.rerun()
    
    # 上一頁按鈕
    with col2:
        if st.button("◀️ 上一頁", disabled=st.session_state.current_page == 1):
            st.session_state.current_page -= 1
            st.rerun()
    
    # 當前頁碼/總頁數顯示
    with col3:
        st.write(f"第 {st.session_state.current_page} / {total_pages} 頁")
    
    # 下一頁按鈕
    with col4:
        if st.button("▶️ 下一頁", disabled=st.session_state.current_page == total_pages):
            st.session_state.current_page += 1
            st.rerun()
    
    # 最後一頁按鈕
    with col5:
        if st.button("⏭️ 最後頁", disabled=st.session_state.current_page == total_pages):
            st.session_state.current_page = total_pages
            st.rerun()
    
    # 計算當前頁的資料範圍
    start_idx = (st.session_state.current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)
    
    # 當前頁的資料
    current_page_df = df.iloc[start_idx:end_idx]
    
    # 顯示當前頁的資料，並處理點擊事件
    selected_row = st.data_editor(
        current_page_df,
        use_container_width=True,
        hide_index=True,
        key=f"data_editor_{st.session_state.current_page}",  # 確保每頁都有唯一的key
        column_config={col: st.column_config.Column(
            width="auto"
        ) for col in current_page_df.columns}
    )
    
    # 顯示資料範圍信息
    st.caption(f'顯示第 {start_idx + 1} 到 {end_idx} 筆，共 {total_rows} 筆')
    
    # 如果啟用了調試模式且有選擇的行
    if show_debug and len(selected_row) > 0:
        st.subheader("選中資料的詳細內容")
        st.json(selected_row.iloc[0].to_dict())

def main():
    st.set_page_config(
        page_title="Elasticsearch 資料瀏覽器",
        layout="wide"
    )

    st.title("Elasticsearch 資料瀏覽器")

    # 初始化 session state
    if 'page_size' not in st.session_state:
        st.session_state.page_size = 50  # 預設為50筆

    # 側邊欄：連接設定
    with st.sidebar:
        st.header("連接設定")
        host = st.selectbox("主機", ["192.168.x.x","192.168.y.y","192.168.z.z"], index=0)
        port = st.number_input("端口", value=9200)
        scheme = st.selectbox("協議", ["http", "https"], index=0)

        try:
            es_client = ElasticsearchClient(host=host, port=port, scheme=scheme)
            
            # 獲取並顯示索引列表
            st.header("索引列表")
            indices = es_client.list_indices()
            selected_index = st.selectbox("選擇索引", indices)

        except Exception as e:
            st.error("無法連接到 Elasticsearch")
            st.stop()

    # 主要內容區域
    if selected_index:
        st.header(f"索引: {selected_index}")

        # 獲取映射信息
        doc_type, mapping = es_client.get_mapping_info(selected_index)
        st.write(f"文檔類型: {doc_type}")
        
        # 文檔內容區域
        st.subheader("文檔內容")
        
        # 顯示調試信息的選項和每頁筆數選擇
        col1, col2 = st.columns([2, 1])
        with col1:
            show_debug = st.checkbox("顯示資料詳細內容")
        with col2:
            # 改變索引或每頁筆數時，重置當前頁碼
            page_size = st.selectbox(
                "每頁顯示筆數",
                options=[20, 50, 100],
                index=1,  # 預設選擇50筆
                key="page_size"
            )
        
        # 搜尋文檔
        documents = es_client.search_documents(selected_index, size=100)
        
        if documents:
            # 轉換為 DataFrame 並顯示
            df = pd.DataFrame(documents)
            
            # 重新排序列，將元數據放在前面，並重命名保留字列名
            meta_columns = ['_id', '_type', '_index']
            data_columns = [col for col in df.columns if col not in meta_columns]
            
            # 重命名列以避免與 Streamlit 保留字衝突
            df = df.rename(columns={
                '_id': 'ID',
                '_type': 'Type',
                '_index': 'Index'
            })
            renamed_meta_columns = ['ID', 'Type', 'Index']
            df = df[renamed_meta_columns + data_columns]
            
            # 使用分頁顯示 DataFrame，並傳入 show_debug 參數
            display_paginated_dataframe(df, page_size, show_debug)
            
            # 下載按鈕區域
            st.write("下載資料：")
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # JSON 下載按鈕 - 使用原始資料
                st.download_button(
                    label="下載為 JSON",
                    data=json.dumps(documents, ensure_ascii=False, indent=2),
                    file_name=f"{selected_index}_data.json",
                    mime="application/json"
                )
            
            with col2:
                # CSV 下載按鈕 - 使用重命名後的 DataFrame
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                
                st.download_button(
                    label="下載為 CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"{selected_index}_data.csv",
                    mime="text/csv"
                )
        else:
            st.info("沒有找到文檔或發生錯誤")
            
        # 顯示映射信息
        #if show_debug and mapping:
        #    st.subheader("索引映射信息")
        #    st.json(mapping)

        # 索引統計移到最下方
        st.subheader("索引統計")
        stats = es_client.get_index_stats(selected_index)
        if stats:
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("文檔數量", stats["文檔數量"])
            with col2:
                st.metric("已刪除文檔", stats["已刪除文檔"])
            with col3:
                st.metric("存儲大小(bytes)", stats["存儲大小(bytes)"])
            with col4:
                st.metric("索引操作次數", stats["索引操作次數"])
            with col5:
                st.metric("搜尋操作次數", stats["搜尋操作次數"])

if __name__ == "__main__":
    main()