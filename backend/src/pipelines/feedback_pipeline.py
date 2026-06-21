import random
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.feedback import CitizenFeedback
from src.repositories.district_repo import DistrictRepo
from src.utils.logger import get_logger

logger = get_logger(__name__)

FEEDBACK_TEMPLATES = [
    ("traffic", "negative", "Tắc đường nghiêm trọng tại giờ cao điểm"),
    ("traffic", "negative", "Ùn tắc kéo dài trên đường Nguyễn Trãi"),
    ("environment", "negative", "Chất lượng không khí kém, ngột ngạt"),
    ("environment", "positive", "Môi trường tốt hơn sau khi trồng cây"),
    ("infrastructure", "negative", "Đường xuống cấp, nhiều ổ gà"),
    ("infrastructure", "positive", "Đèn đường mới hoạt động tốt"),
    ("flood", "negative", "Ngập úng sau mưa lớn"),
    ("safety", "positive", "Khu vực an ninh, an toàn"),
]


class FeedbackPipeline:
    @staticmethod
    async def run(session: AsyncSession) -> None:
        districts = await DistrictRepo.get_all(session)
        timestamp = datetime.now(timezone.utc)

        for district in districts:
            num_feedback = random.randint(2, 5)
            for _ in range(num_feedback):
                template = random.choice(FEEDBACK_TEMPLATES)
                feedback = CitizenFeedback(
                    city_id=district.city_id,
                    district_id=district.id,
                    category=template[0],
                    sentiment=template[1],
                    content=template[2],
                    created_at=timestamp,
                )
                session.add(feedback)
        await session.commit()
        logger.info(f"Generated feedback for {len(districts)} districts")
