import { ResourcesList } from '@/components/feed-resources-list'
import { createClient } from '@/lib/supabase/server'
import { cookies } from 'next/headers'

export default async function Page() {
  const supabase = await createClient(cookies())
  const { data: resources } = await supabase.from('resources').select('*, tags(*)')
  return <ResourcesList resources={resources || []} />
}
