import { lazy, Suspense, type ComponentProps } from 'react';

const LeafletSceneMap = lazy(() =>
  import('./LeafletSceneMap').then((module) => ({ default: module.SceneMap })),
);

export function SceneMap(props: ComponentProps<typeof LeafletSceneMap>) {
  return (
    <Suspense
      fallback={
        <div className={`scene-map-wrap ${props.compact ? 'scene-map-compact' : ''}`}>
          <div className="scene-map" role="status">
            Загружаем карту…
          </div>
        </div>
      }
    >
      <LeafletSceneMap {...props} />
    </Suspense>
  );
}
