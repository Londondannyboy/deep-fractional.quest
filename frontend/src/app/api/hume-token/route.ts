import { NextResponse } from "next/server";

/**
 * Generate Hume access token using OAuth2 client credentials.
 *
 * Required environment variables:
 * - HUME_API_KEY
 * - HUME_SECRET_KEY
 */
export async function GET() {
  const apiKey = process.env.HUME_API_KEY;
  const secretKey = process.env.HUME_SECRET_KEY;

  if (!apiKey || !secretKey) {
    console.error("[HUME-TOKEN] Missing HUME_API_KEY or HUME_SECRET_KEY");
    return NextResponse.json(
      { error: "Hume credentials not configured" },
      { status: 500 }
    );
  }

  try {
    // OAuth2 client credentials flow
    const authString = Buffer.from(`${apiKey}:${secretKey}`).toString("base64");

    const response = await fetch("https://api.hume.ai/oauth2-cc/token", {
      method: "POST",
      headers: {
        Authorization: `Basic ${authString}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        grant_type: "client_credentials",
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("[HUME-TOKEN] Token request failed:", errorText);
      return NextResponse.json(
        { error: "Failed to get Hume token" },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      accessToken: data.access_token,
    });
  } catch (error) {
    console.error("[HUME-TOKEN] Error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
