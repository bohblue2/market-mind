import type { Metadata } from 'next'
import Image from 'next/image'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import styles from '@/styles/markdown.module.css'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import {
  ArrowLeftIcon,
  BookmarkIcon,
  ExternalLinkIcon,
  ShareIcon,
} from 'lucide-react'

import { PaneContainer, PaneContent, PaneHeader } from '@/components/pane'
import { badgeVariants } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

import { formatDate } from '@/lib/utils'
import { createClient } from '@/lib/supabase/server'
import { cookies } from 'next/headers'

interface Props {
  params: {
    id: string
  }
  searchParams: {
    tag: string
  }
}

export default async function Page({ params, searchParams }: Props) {
  const supabase = await createClient(cookies())
  const { data: resource } = await supabase
    .from('resources')
    .select('*, tags(*)')
    .eq('id', params.id)
    .single()

  if (!resource) {
    throw notFound()
  }
  // Validate the URL
  const isValidUrl = (url: string) => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  return (
    <PaneContainer>
      <PaneHeader className="justify-between xl:px-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href={searchParams.tag ? `/tags/${searchParams.tag}` : '/'}>
            <ArrowLeftIcon size={16} />
          </Link>
        </Button>
        <div className="flex space-x-1">
          <Button variant="ghost" size="icon" disabled>
            <ShareIcon size={16} />
          </Button>
          <Button variant="ghost" size="icon" disabled>
            <BookmarkIcon size={16} />
          </Button>
        </div>
      </PaneHeader>
      <PaneContent>
        <div className="px-2 py-4 xl:px-3 xl:py-7">
          <div className="grid grid-cols-1 gap-4 xl:gap-8 2xl:grid-cols-3 2xl:flex-row">
            <div className="2xl:col-span-2">
              <div className="flex w-full flex-col space-y-4 text-muted-foreground">
                <div className="flex items-center justify-between space-x-2 text-xs text-muted-foreground">
                  <div className="flex space-x-2">
                    {resource.tags.map((tag) => (
                      <Link
                        className={badgeVariants({ variant: 'secondary' })}
                        href={`/tags/${tag.slug}`}
                        key={tag.slug}
                      >
                      </Link>
                    ))}
                  </div>
                  <span>{formatDate(resource.created_at)}</span>
                </div>
                <div className="space-y-4">
                  {isValidUrl(resource.url) ? (
                    <Link
                      className="flex flex-col transition-colors hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      href={resource.url}
                      target="_blank"
                    >
                      <h1 className="text-xl text-foreground">
                        {resource.title}
                      </h1>
                      <div className="flex items-center space-x-1 text-sm">
                        <ExternalLinkIcon size={14} />
                        <span>{new URL(resource.url).hostname}</span>
                      </div>
                    </Link>
                  ) : (
                    <p>Invalid URL</p>
                  )}
                  <div className={styles.markdown}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{resource.description}</ReactMarkdown>
                  </div>
                </div>
              </div>
            </div>
            <div className="order-first 2xl:order-last 2xl:col-span-1">
              <div className="flex w-full justify-center">
                {resource.thumbnail && (
                  <Link
                    className="relative inline-flex overflow-hidden rounded-lg bg-secondary"
                    href={resource.url}
                    target="_blank"
                  >
                    <Image
                      src={resource.thumbnail}
                      alt={resource.title}
                      width={1024}
                      height={537}
                      unoptimized
                    />
                  </Link>
                )}
              </div>
            </div>
          </div>
        </div>
      </PaneContent>
    </PaneContainer>
  )
}
