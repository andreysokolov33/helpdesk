type CompressOpts = {
  maxDim?: number;
  quality?: number;
};

function fileExt(name: string): string {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i + 1).toLowerCase() : "";
}

/**
 * Сжимает изображение в WebP с даунскейлом.
 * Ошибки/неподдерживаемые форматы → исходный File (без throw).
 */
export async function compressImageToWebp(file: File, opts?: CompressOpts): Promise<File> {
  const maxDim = opts?.maxDim ?? 1920;
  const quality = opts?.quality ?? 0.82;
  const ext = fileExt(file.name);
  if (!file.type.startsWith("image/") && !["jpg", "jpeg", "png", "gif", "webp", "bmp"].includes(ext)) {
    return file;
  }
  // SVG и прочее без растрового decode — не трогаем
  if (file.type === "image/svg+xml" || ext === "svg") return file;

  let bitmap: ImageBitmap | null = null;
  try {
    bitmap = await createImageBitmap(file).catch(() => null);
    if (!bitmap) return file;

    const w = bitmap.width;
    const h = bitmap.height;
    if (!Number.isFinite(w) || !Number.isFinite(h) || w < 1 || h < 1) return file;

    const scale = Math.min(1, maxDim / Math.max(w, h));
    const tw = Math.max(1, Math.round(w * scale));
    const th = Math.max(1, Math.round(h * scale));

    // Повторный decode сразу в целевой размер — меньше пик памяти на больших фото
    if (scale < 0.95) {
      bitmap.close();
      bitmap = null;
      bitmap = await createImageBitmap(file, {
        resizeWidth: tw,
        resizeHeight: th,
        resizeQuality: "high",
      }).catch(() => null);
      if (!bitmap) return file;
    }

    const canvas = document.createElement("canvas");
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return file;
    ctx.drawImage(bitmap, 0, 0);

    const blob: Blob | null = await new Promise((resolve) => {
      try {
        canvas.toBlob((b) => resolve(b), "image/webp", quality);
      } catch {
        resolve(null);
      }
    });
    if (!blob || blob.size < 1) return file;

    const nameBase = (file.name || "image").replace(/\.[^.]+$/, "") || "image";
    return new File([blob], `${nameBase}.webp`, { type: "image/webp", lastModified: Date.now() });
  } catch {
    return file;
  } finally {
    try {
      bitmap?.close();
    } catch {
      /* ignore */
    }
  }
}
