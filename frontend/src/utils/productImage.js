// Display-only mapping: never write local URLs back into product data.
const localDemo = import.meta.env.VITE_LOCAL_PRODUCT_IMAGES === 'true';

export function productImageSource(product) {
  const image = product?.main_image || '';
  if (!localDemo) return image;

  // Preserve registered uploads from this local site's GCS emulator.
  if (image) {
    try {
      if (new URL(image, window.location.origin).origin === window.location.origin) return image;
    } catch {
      // Invalid or external legacy URLs use local files, never external fallback.
    }
  }

  const id = Number(product?.product_id);
  return Number.isSafeInteger(id) && id > 0 ? `/images/products/product-${id}` : '';
}
