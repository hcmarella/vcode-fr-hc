import { useQuery } from "@tanstack/react-query";
import { ReactNode } from "react";

import { imagesApi } from "../../api/images";
import { ApiError } from "../../api/client";

interface HeroBannerProps {
  imageQuery: string;
  children: ReactNode;
}

// Falls back to the plain gradient (no network call retried, no broken-image
// flash) whenever PEXELS_API_KEY isn't configured -- image search is a
// progressive enhancement here, never a hard dependency for the dashboard to
// render.
export default function HeroBanner({ imageQuery, children }: HeroBannerProps) {
  const { data: images } = useQuery({
    queryKey: ["images", imageQuery],
    queryFn: () => imagesApi.search(imageQuery, 1),
    retry: false,
    staleTime: Infinity, // one photo for the session is plenty -- no reason to refetch on every navigation back to Home
    throwOnError: (error) => !(error instanceof ApiError && error.status === 503),
  });
  const photo = images?.[0];

  return (
    <div className="relative animate-fade-in-up overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8 text-white shadow-sm">
      {photo && (
        <>
          <img
            src={photo.url}
            alt={photo.alt}
            className="absolute inset-0 h-full w-full object-cover opacity-30"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-slate-900/95 via-slate-900/80 to-slate-900/60" />
          <a
            href={photo.photographer_url}
            target="_blank"
            rel="noreferrer"
            className="absolute bottom-2 right-3 z-10 text-[10px] text-white/40 hover:text-white/70"
          >
            Photo by {photo.photographer} on Pexels
          </a>
        </>
      )}
      <div className="relative z-10">{children}</div>
    </div>
  );
}
