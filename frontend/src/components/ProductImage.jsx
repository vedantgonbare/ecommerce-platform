import { useState } from 'react'

function ProductImage({ src, alt }) {
  const [failed, setFailed] = useState(false)

  return (
    <div className="aspect-4/3 w-full overflow-hidden bg-surface">
      {src && !failed && (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          onError={() => setFailed(true)}
          className="h-full w-full object-cover"
        />
      )}
    </div>
  )
}

export default ProductImage