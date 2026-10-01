import { useEffect, useState } from 'react';
import { authenticated_fetch } from '../api/client';
import { use_auth } from '../features/auth/AuthProvider';

export function Cover({
  url,
  name,
  large = false,
}: {
  url?: string | null;
  name: string;
  large?: boolean;
}) {
  const [failed_url, set_failed_url] = useState<string | null>(null);
  const [private_image, set_private_image] = useState<{
    url: string;
    blob_url: string;
    user_id: number;
  } | null>(null);
  const { user } = use_auth();
  const requires_auth = !!user && !!url?.startsWith('/api/v1/media/');
  useEffect(() => {
    if (!requires_auth || !url || !user) return;
    const controller = new AbortController();
    let blob_url: string | undefined;
    void authenticated_fetch(
      new Request(new URL(url, window.location.origin), { signal: controller.signal }),
    )
      .then(async (response) => {
        if (!response.ok) throw new Error('image');
        const blob = await response.blob();
        if (controller.signal.aborted) return;
        blob_url = URL.createObjectURL(blob);
        set_private_image({ url, blob_url, user_id: user.id });
      })
      .catch(() => {
        if (!controller.signal.aborted) set_failed_url(url);
      });
    return () => {
      controller.abort();
      if (blob_url) URL.revokeObjectURL(blob_url);
    };
  }, [url, user?.id, requires_auth]);
  const image_url = requires_auth
    ? private_image && private_image.url === url && private_image.user_id === user?.id
      ? private_image.blob_url
      : null
    : url;
  return (
    <div className={`cover ${large ? 'cover-large' : ''}`}>
      {image_url && url !== failed_url ? (
        <img
          src={image_url}
          alt={`Обложка: ${name}`}
          loading="lazy"
          onError={() => set_failed_url(url || null)}
        />
      ) : (
        <span aria-hidden="true">♫</span>
      )}
    </div>
  );
}
