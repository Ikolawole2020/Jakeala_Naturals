"use client";

import { useState } from "react";
import { imageUrl } from "@/lib/api";

export default function ProductGallery({ images, name }) {
  const list = images && images.length ? images : [null];
  const [i, setI] = useState(0);

  return (
    <div className="gallery">
      <div className="main">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={imageUrl(list[i]) || "/logo.png"} alt={name} />
      </div>
      {list.length > 1 && (
        <div className="thumbs">
          {list.map((src, idx) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              key={idx}
              src={imageUrl(src) || "/logo.png"}
              alt={`View of ${name}`}
              className={idx === i ? "on" : ""}
              onClick={() => setI(idx)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
