import { ResourcesList } from '@/components/feed-resources-list'
import { createClient } from '@/lib/supabase/server'
import { cookies } from 'next/headers'

export default async function Default() {
  const supabase = await createClient(cookies())
  const { data: resources } = await supabase
    .from('resources')
    .select('*, tags(*)')
    .order('created_at', { ascending: false })
  return <ResourcesList resources={resources || []} />
}
