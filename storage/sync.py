import json
import requests
import math
import time
import hashlib
import logging

# 配置日志
logger = logging.getLogger(__name__)

def generate_sign(body):
    """生成API签名"""
    try:
        app_name = "mathmagic"
        app_key = "82be0592545283da00744b489f758f99"
        sid = "mathmagic"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        timestamp = str(int(time.time()))
        sign_str = f"{app_key}appName{app_name}body{body}sid{sid}timestamp{timestamp}{app_key}"
        sign = hashlib.md5(sign_str.encode()).hexdigest()
        
        params = {
            "appName": app_name,
            "sid": sid,
            "sign": sign,
            "timestamp": timestamp,
        }
        logger.info(f"生成签名成功: params={params}")
        return params, headers
    except Exception as e:
        logger.error(f"生成签名失败: {str(e)}")
        raise

def sync_stock_data(page=1):
    """同步库存数据"""
    try:
        logger.info(f"开始同步第 {page} 页数据")
        body = {
            "page_size": 100,
            "page_no": page,
            "warehouseNo": "7",
            "warehouseType": 1,
            "employeeId": 1
        }
        
        body_str = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        params, headers = generate_sign(body_str)
        url = "https://openapi.qizhishangke.com/api/openservices/stockSpec/v1/getStockSpecList"
        
        # 添加重试机制
        for attempt in range(3):
            try:
                logger.info(f"尝试第 {attempt + 1} 次请求API")
                response = requests.post(url, params=params, headers=headers, data=body_str)
                break
            except Exception as e:
                logger.error(f"API请求失败 (尝试 {attempt + 1}): {str(e)}")
                if attempt < 2:
                    time.sleep(15)
                    continue
                raise
        
        data = response.json()
        if data['code'] != 200:
            logger.error(f"API返回错误: {data}")
            raise Exception(f"API返回错误: {data['message']}")
        
        result = data['data']
        logger.info(f"成功获取数据: 总数={result['total']}, 当前页={result['currentPage']}")
        
        return {
            'items': result['data'],
            'total': result['total'],
            'current_page': result['currentPage'],
            'max_page': math.ceil(result['total'] / result['pageSize'])
        }
    except Exception as e:
        logger.error(f"同步数据失败: {str(e)}")
        raise

def update_stock_data(stock_data):
    """更新库存数据到数据库"""
    try:
        # logger.info(f"开始更新库存数据: {len(stock_data['items'])} 条记录")
        from .models import Stock, Warehouse
        from gallery.models import SKU
        
        updated_count = 0
        skipped_count = 0
        for item in stock_data['items']:
            try:
                # 尝试获取SKU，不存在则跳过
                try:
                    sku = SKU.objects.get(sku_code=item['specNo'])
                except SKU.DoesNotExist:
                    # logger.warning(f"SKU不存在，跳过更新: {item['specNo']}")
                    skipped_count += 1
                    continue
                
                # 获取或创建仓库
                warehouse, wh_created = Warehouse.objects.get_or_create(
                    name=item['warehouseName']
                )
                
                # 更新库存信息
                stock, stock_created = Stock.objects.update_or_create(
                    sku=sku,
                    warehouse=warehouse,
                    defaults={
                        'stock_num': item['stockNum'],
                        'avg_cost': item['avgCost']
                    }
                )
                updated_count += 1
                
            except Exception as e:
                # logger.error(f"更新单条记录失败: SKU={item['specNo']}, 错误={str(e)}")
                continue
        
        # logger.info(f"成功更新 {updated_count} 条记录，跳过 {skipped_count} 条记录")
        
    except Exception as e:
        # logger.error(f"更新库存数据失败: {str(e)}")
        raise

def sync_all_stock():
    """同步所有库存数据"""
    try:
        page = 1
        total_updated = 0
        
        while True:
            # 获取当前页数据
            stock_data = sync_stock_data(page)
            
            # 更新到数据库
            update_stock_data(stock_data)
            total_updated += len(stock_data['items'])
            
            # 检查是否还有下一页
            if page >= stock_data['max_page']:
                break
            
            # 继续下一页
            page += 1
            time.sleep(10)  # 避免请求过快
        
        logger.info(f"同步完成，共更新 {total_updated} 条记录")
        
    except Exception as e:
        logger.error(f"同步过程中断: {str(e)}")
        raise