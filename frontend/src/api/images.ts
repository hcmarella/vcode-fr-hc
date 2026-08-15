import { apiClient } from "./client";

export interface ImageResult {
  id: number;
  url: string;
  alt: string;
  photographer: string;
  photographer_url: string;
}

export const imagesApi = {
  // Nothing here is ever persisted -- see backend/app/api/images.py. The
  // frontend just hotlinks whatever URL comes back for the duration of the
  // page view.
  search: (query: string, perPage = 6) =>
    apiClient.get<ImageResult[]>(
      `/api/images/search?query=${encodeURIComponent(query)}&per_page=${perPage}`
    ),
};
