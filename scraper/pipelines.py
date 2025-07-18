from news.models import News, Tag
from django.db.utils import IntegrityError
from django.db import transaction
from asgiref.sync import sync_to_async
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)


class DjangoNewsPipeline:
    async def process_item(self, item, spider):
        try:
            await sync_to_async(self.process_item_sync)(item)
        except Exception as e:
            logger.error(f"Error processing {item['source']}: {e}")
        return item

    def process_item_sync(self, item):
        try:
            with transaction.atomic():
                tehran_tz = ZoneInfo("Asia/Tehran")
                news, created = News.objects.get_or_create(
                    source=item['source'],
                    defaults={
                        'title': item['title'],
                        'content': item['content'],
                        'published_at': item['published_at'].replace(tzinfo=tehran_tz),
                        'is_active': item['is_active'],
                    }
            )

            if created:
                for tag_name in item.get('tags', []):
                    clean_name = tag_name.strip()
                    if not clean_name:
                        continue

                    tag, tag_created = Tag.objects.get_or_create(
                        name=clean_name,
                        defaults={'slug': clean_name.strip().lower().replace(' ', '-')}
                    )

                    news.tags.add(tag)

                    if tag_created:
                        logger.info(f"  Created Tag: {clean_name}")
                    else:
                        logger.debug(f"  Reused Tag:  {clean_name}")

                logger.info(f"Created News: {item['title']}")

            else:
                logger.debug(f"Skipped existing News: {item['title']}")

        except IntegrityError as e:
            logger.error(f"Integrity Error for {item['source']}: {e}")
        except Exception as e:
            logger.error(f"Error processing {item['source']}: {e}")
            raise
        return item
