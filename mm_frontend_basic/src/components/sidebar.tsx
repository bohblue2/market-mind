import Image from 'next/image'
import Link from 'next/link'

import { GitHubLogoIcon } from '@radix-ui/react-icons'
import {
  BookmarkIcon,
  BracesIcon,
  CalendarIcon,
  ExternalLinkIcon,
  LayoutTemplateIcon,
  LogOutIcon,
  MegaphoneIcon,
  MonitorSmartphoneIcon,
  Package2Icon,
  PanelTopIcon,
  PinIcon,
  PlusIcon,
  StickyNoteIcon,
} from 'lucide-react'

import { PaneContainer, PaneContent, PaneHeader } from './pane'
import { SidebarClient } from './sidebar-client'
import { NavItem } from './sidebar-nav-item'
import { SidebarToggle } from './sidebar-toggle'
import { SubmitResourceForm } from './submit-resource-form'
import { Button } from './ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog'
import { createClient } from '@/lib/supabase/server'
import { cookies } from 'next/headers'

const externalLinks = [
  // {
  //   label: 'About Us',
  //   href: 'https://naver.com',
  // },
]

function getTagIcon(slug: string) {
  switch (slug) {
    case 'official':
      return MegaphoneIcon
    case 'tutorials':
      return MonitorSmartphoneIcon
    case 'packages':
      return Package2Icon
    case 'events':
      return CalendarIcon
    case 'showcase':
      return PanelTopIcon
    case 'templates':
      return LayoutTemplateIcon
    case 'examples':
      return BracesIcon
    case 'opinions':
      return StickyNoteIcon
    default:
      return PinIcon
  }
}

export async function Sidebar() {
  const supabase = await createClient(cookies())
  const session = await supabase.auth.getUser()
  const { data: tags } = await supabase.from('tags').select('*, resources(id)')

  return (
    <SidebarClient>
      <PaneContainer className="max-h-screen overflow-y-auto">
        {/* Brand */}
        <PaneHeader className="justify-between">
          <Link
            className="inline-flex items-center space-x-3 px-1 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring xl:p-0"
            href="/"
          >
            <BookmarkIcon size={20} />
            <span>에지 - Ai Zzirasi</span>
          </Link>
          <SidebarToggle />
        </PaneHeader>
        <PaneContent>
          <nav className="flex flex-1 flex-col divide-y divide-border text-muted-foreground">
            {/* User section */}
            {session.data?.user && (
              <div className="space-y-0.5 py-2 xl:py-4">
                <div className="flex h-9 items-center justify-between space-x-3 px-2 text-sm xl:px-3">
                  <div className="flex items-center space-x-3">
                    <Image
                      className="rounded-full"
                      src={session.data.user.user_metadata.avatar_url!}
                      alt="User Avatar"
                      width={16}
                      height={16}
                      unoptimized
                    />
                    <span>{session.data.user.user_metadata.name}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    {/* Submit a resource */}
                    <Dialog>
                      <DialogTrigger asChild>
                        <button className="inline-flex size-4 transition-colors hover:text-accent-foreground">
                          <PlusIcon size={16} />
                        </button>
                      </DialogTrigger>
                      <DialogContent className="max-w-md">
                        <DialogHeader>
                          <DialogTitle>Submit a resource</DialogTitle>
                          <DialogDescription>
                            We will review your submission and add it to our
                            collection within 24 hours.
                          </DialogDescription>
                        </DialogHeader>
                        <SubmitResourceForm />
                      </DialogContent>
                    </Dialog>
                    {/* Sign out */}
                    {/* <form className="inline-flex" action={signOut}>
                      <button className="inline-flex size-4 transition-colors hover:text-accent-foreground">
                        <LogOutIcon size={16} />
                      </button>
                    </form> */}
                  </div>
                </div>
              </div>
            )}

            {/* Tags */}
            {tags && tags.length > 0 && (
              <div className="space-y-0.5 py-2 xl:py-4">
                <div className="flex h-9 items-center px-2 xl:px-3">
                  <span className="text-sm">Menu</span>
                </div>
                {tags.map((tag) => {
                  const TagIcon = getTagIcon(tag.slug)
                  return (
                    <NavItem
                      className="justify-between"
                      href={`/tags/${tag.slug}`}
                      tag={tag.slug}
                      key={tag.slug}
                      prefetch
                    >
                      <div className="flex items-center space-x-3">
                        <TagIcon size={16} />
                        <span>{tag.name}</span>
                      </div>
                      <span>{tag.resources.length}</span>
                    </NavItem>
                  )
                })}
              </div>
            )}
            {/* External links */}
            {/* <div className="space-y-0.5 py-2 xl:mt-auto xl:py-4">
              {externalLinks.map((item) => (
                <NavItem href={item.href} target="_blank" key={item.href}>
                  <ExternalLinkIcon size={16} />
                  <span>{item.label}</span>
                </NavItem>
              ))}
            </div> */}

            {/* Sign in */}
            {!session.data?.user && (
              <div className="p-2">
                <form
                // action={signInWithGithub}
                >
                  <Button type="submit" className="w-full" variant="ghost">
                    <GitHubLogoIcon className="size-4" />
                    <span>Signin with GitHub</span>
                  </Button>
                </form>
              </div>
            )}
          </nav>
        </PaneContent>
      </PaneContainer>
    </SidebarClient>
  )
}
