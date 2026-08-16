import "./index.css";
import { Composition } from "remotion";
import { CinematicPromo, CinematicPromoProps, calculateCinematicPromoMetadata } from "./CinematicPromo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="CinematicPromo"
        component={CinematicPromo}
        durationInFrames={360} // default fallback (15s @ 24fps)
        fps={24}
        width={1280}
        height={720}
        schema={null}
        calculateMetadata={calculateCinematicPromoMetadata}
        defaultProps={{
          bgImages: [],
          logoPath: "",
          colors: {
            bg: "#0a0a0c",
            primary: "#00CFFF",
            secondary: "#7B4FD6"
          },
          durationInSeconds: 15
        } as CinematicPromoProps}
      />
    </>
  );
};
