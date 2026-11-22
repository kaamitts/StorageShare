import { useEffect } from 'react';
import L from 'leaflet';
import { MapContainer, Marker, Popup, TileLayer, CircleMarker, useMap, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

const ALMATY = [43.2389, 76.8897];
L.Marker.prototype.options.icon = L.icon({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function MapClickHandler({ onPick }) {
  useMapEvents({ click: event => onPick?.(event.latlng) });
  return null;
}

function MapBaseLayer({ lang }) {
  const map = useMap();
  const apiKey = import.meta.env.VITE_MAPTILER_API_KEY;
  useEffect(() => {
    if (!apiKey) return undefined;
    let layer;
    let disposed = false;
    import('@maptiler/leaflet-maptilersdk').then(({ Language, MapStyle, MaptilerLayer }) => {
      if (disposed) return;
      const language = lang === 'kk' ? Language.KAZAKH : lang === 'ru' ? Language.RUSSIAN : Language.ENGLISH;
      layer = new MaptilerLayer({ apiKey, style: MapStyle.STREETS, language });
      layer.addTo(map);
    });
    return () => { disposed = true; layer?.remove(); };
  }, [apiKey, lang, map]);
  return apiKey ? null : <TileLayer
    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
  />;
}

function MapViewport({ points, selectedPosition, focusPosition, userPosition }) {
  const map = useMap();
  useEffect(() => {
    if (focusPosition) {
      map.setView(focusPosition, 16, { animate: true });
      return;
    }
    if (userPosition) {
      map.setView(userPosition, 14, { animate: true });
      return;
    }
    if (selectedPosition) {
      map.setView(selectedPosition, 15, { animate: true });
      return;
    }
    const locations = points
      .filter(point => point.latitude != null && point.longitude != null)
      .map(point => [Number(point.latitude), Number(point.longitude)]);
    if (locations.length > 1) map.fitBounds(L.latLngBounds(locations), { padding: [30, 30] });
    else if (locations.length === 1) map.setView(locations[0], 14);
  }, [map, points, selectedPosition, focusPosition, userPosition]);
  return null;
}

export default function StorageMap({
  points = [], onPick, selectedPosition = null, focusPosition = null,
  userPosition = null, locationLabel, lang = 'en',
}) {
  return <MapContainer className="storage-map" center={ALMATY} zoom={12} scrollWheelZoom>
    <MapBaseLayer lang={lang} />
    <MapClickHandler onPick={onPick} />
    <MapViewport points={points} selectedPosition={selectedPosition}
      focusPosition={focusPosition} userPosition={userPosition} />
    {points.filter(point => point.latitude != null && point.longitude != null).map(point =>
      <Marker key={point.id} position={[Number(point.latitude), Number(point.longitude)]}>
        <Popup>{point.popupContent || point.name}</Popup>
      </Marker>)}
    {selectedPosition && <Marker position={selectedPosition} />}
    {userPosition && <CircleMarker center={userPosition} radius={8} pathOptions={{ color: '#2563eb', fillOpacity: 0.8 }}>
      <Popup>{locationLabel}</Popup>
    </CircleMarker>}
  </MapContainer>;
}
