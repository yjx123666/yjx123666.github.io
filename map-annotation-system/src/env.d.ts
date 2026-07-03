/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>
  export default component
}

declare module '@geoman-io/leaflet-geoman-free' {
  import L from 'leaflet'

  namespace PM {
    interface MapDrawOptions {
      marker?: boolean
      polyline?: boolean
      polygon?: boolean
      rectangle?: boolean
      circle?: boolean
      circleMarker?: boolean
    }

    interface AddControlsOptions {
      position?: string
      drawMarker?: boolean
      drawPolyline?: boolean
      drawPolygon?: boolean
      drawRectangle?: boolean
      drawCircle?: boolean
      drawCircleMarker?: boolean
      editMode?: boolean
      dragMode?: boolean
      cutPolygon?: boolean
      removalMode?: boolean
      rotateMode?: boolean
    }

    interface Map {
      pm: {
        addControls(options?: AddControlsOptions): void
        removeControls(): void
        setLang(lang: string): void
        enableDraw(shape: string, options?: Record<string, unknown>): void
        disableDraw(): void
      }
    }
  }
}

declare module 'leaflet' {
  interface Map {
    pm: {
      addControls(options?: Record<string, unknown>): void
      removeControls(): void
      setLang(lang: string): void
      enableDraw(shape: string, options?: Record<string, unknown>): void
      disableDraw(): void
    }
  }
}
