import { ResourcesList } from '@/components/feed-resources-list'
import { createClient } from '@/lib/supabase/server'
import { cookies } from 'next/headers'

interface Props {
  searchParams: {
    tag: string
  }
}

export default async function Page({ searchParams }: Props) {
  const supabase = await createClient(cookies())
  const { data: resources } = await supabase
    .from('resources')
    .select('*, tags(*)')
    .order('created_at', { ascending: false })
  return (
    <ResourcesList
      resources={resources?.filter((resource) => resource.tags.some((tag) => tag.slug === searchParams.tag)) || []}
    />
  )
}
