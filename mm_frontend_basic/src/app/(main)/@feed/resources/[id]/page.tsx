import { ResourcesList } from '@/components/feed-resources-list'
import { createClient } from '@/lib/supabase/server'
import { cookies } from 'next/headers'
import { notFound } from 'next/navigation'

interface Props {
  params: {
    id: string
  }
}

export default async function Page({ params }: Props) {
  const supabase = await createClient(cookies())

  const { data: currentResourceTags } = await supabase
    .from('resource_tags')
    .select('tag_id')
    .eq('resource_id', params.id)

  if (!currentResourceTags) {
    throw notFound()
  }

  const tagIds = currentResourceTags.map(tag => tag.tag_id)

  const { data: relatedResources } = await supabase
    .from('resources')
    .select('*, resource_tags(*)')
    .in('id', (
      await supabase
        .from('resource_tags')
        .select('resource_id')
        .in('tag_id', tagIds)
        .then(({ data }) => data?.map(r => r.resource_id) || [])
    ))
    .order('created_at', { ascending: false })

  if (!relatedResources?.length) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground">
        <span>No resources found.</span>
      </div>
    )
  }

  return <ResourcesList resources={relatedResources} />
}