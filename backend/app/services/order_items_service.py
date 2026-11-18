from fastapi import HTTPException
from app.crud.order_items import get_all_order_items, get_order_item, get_order_items_by_order_id
from app.crud.orders import get_order


async def create_order_item_service(*args, **kwargs):
    raise HTTPException(status_code=409, detail="明細只能經購物車轉單交易建立")


async def update_order_item_service(*args, **kwargs):
    raise HTTPException(status_code=409, detail="不可直接修改歷史明細")


async def delete_order_item_service(*args, **kwargs):
    raise HTTPException(status_code=409, detail="不可刪除歷史明細")


async def get_all_order_items_service(db, current_user):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="僅限 Admin")
    return await get_all_order_items(db)


async def get_authorized_order_item(db, item_id, current_user):
    item = await get_order_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="訂單項目不存在")
    if (current_user.role_id == 1 or item.order.user_id == current_user.user_id
            or (current_user.role_id == 2 and item.seller_id == current_user.user_id)):
        return item
    raise HTTPException(status_code=403, detail="無權查看此明細")


async def get_order_items_by_order_service(db, current_user, order_id, sales=False):
    order = await get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    items = await get_order_items_by_order_id(db, order_id)
    if not sales and (current_user.role_id == 1 or order.user_id == current_user.user_id):
        return items
    if current_user.role_id == 2:
        owned = [item for item in items if item.seller_id == current_user.user_id]
        if owned:
            return owned
    raise HTTPException(status_code=403, detail="無權查看此訂單")
