type CompressOpts = {
  maxDim?: number;
  quality?: number;
};

function fileExt(name: string): string {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i + 1).toLowerCase() : "";
}

export async function compressImageToWebp(file: File, opts?: CompressOpts): Promise<File> {
  const maxDim = opts?.maxDim ?? 2200;
  const quality = opts?.quality ?? 0.85;
  const ext = fileExt(file.name);
  if (!file.type.startsWith("image/") && !["jpg", "jpeg", "png", "gif", "webp", "bmp"].includes(ext)) return file;

  const bitmap = await createImageBitmap(file).catch(() => null);
  if (!bitmap) return file;

  const w = bitmap.width;
  const h = bitmap.height;
  const scale = Math.min(1, maxDim / Math.max(w, h));
  const tw = Math.max(1, Math.round(w * scale));
  const th = Math.max(1, Math.round(h * scale));

  const canvas = document.createElement("canvas");
  canvas.width = tw;
  canvas.height = th;
  const ctx = canvas.getContext("2d");
  if (!ctx) return file;
  ctx.drawImage(bitmap, 0, 0, tw, th);

  const blob: Blob | null = await new Promise((resolve) =>
    canvas.toBlob((b) => resolve(b), "image/webp", quality),
  );
  if (!blob) return file;

  const nameBase = file.name.replace(/\.[^.]+$/, "");
  return new File([blob], `${nameBase || "image"}.webp`, { type: "image/webp" });
}

