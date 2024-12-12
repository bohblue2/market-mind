
from datetime import datetime
from mm_llm.config import settings
from supabase import Client, create_client

from mm_llm.constant import KST

supabase: Client = create_client(settings.PUBLIC_SUPABASE_URL, settings.PUBLIC_SUPABASE_ANON_KEY)

# Add a new post with tags
def add_post_with_tags(post, tag_ids):
    # Insert the new post
    post_data = {
        "title": post["title"],
        "description": post["description"],
        "thumbnail": post["thumbnail"],
        "url": post["url"],
        "is_published": post["is_published"],
        "author_id": post["author_id"],
    }
    response = supabase.table("resources").insert(post_data).execute()
    post_id = response.data[0]["id"]

    # Link tags to the post
    resource_tags = [{"resource_id": post_id, "tag_id": tag_id} for tag_id in tag_ids]
    supabase.table("resource_tags").insert(resource_tags).execute()
    return post_id

# Add a new tag to an existing post
def add_tag_to_post(post_id, tag_name):
    # Check if the tag already exists, insert if not
    tag_response = supabase.table("tags").select("*").eq("name", tag_name).execute()
    if tag_response.data:
        tag_id = tag_response.data[0]["id"]
    else:
        tag_data = {
            "name": tag_name,
            "slug": tag_name.replace(" ", "-").lower(),
            "updated_at": datetime.now(tz=KST).isoformat(),
        }
        tag_response = supabase.table("tags").insert(tag_data).execute()
        tag_id = tag_response.data[0]["id"]

    # Link the tag to the post
    supabase.table("resource_tags").insert({"resource_id": post_id, "tag_id": tag_id}).execute()
    return tag_id

# Add a tag independently
def add_tag_independently(tag_name):
    # Check if the tag already exists
    existing_tag = supabase.table("tags").select("*").eq("name", tag_name.replace(" ", "-").lower().strip()).execute().data
    if existing_tag:
        return existing_tag[0]["id"]
    tag_data = {
        "name": tag_name.replace(" ", "-").lower().strip(), 
        "slug": tag_name.replace(" ", "-").lower().strip(),
        "updated_at": datetime.now(tz=KST).isoformat(),
    }
    response = supabase.table("tags").insert(tag_data).execute()
    return response.data