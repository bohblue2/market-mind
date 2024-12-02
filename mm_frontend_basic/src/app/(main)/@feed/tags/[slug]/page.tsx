import { ResourcesList } from '@/components/feed-resources-list'
import { createClient } from '@/lib/supabase/server'
import { cookies } from 'next/headers'

interface Props {
  params: {
    slug: string
  }
}

export default async function Page({ params }: Props) {
  const supabase = await createClient(cookies())
  const { data: resources } = await supabase
    .from('resources')
    .select('*, tags(*)')
    .order('created_at', { ascending: false })
  return (
    <ResourcesList
      resources={resources?.filter((resource) => resource.tags.some((tag) => tag.slug === params.slug)) || []}
    />
  )
}
