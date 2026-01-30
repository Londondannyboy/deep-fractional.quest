import { NextRequest, NextResponse } from 'next/server';

const ZEP_API_KEY = process.env.ZEP_API_KEY || '';
// Graph name for Zep knowledge graph - set in Vercel/Railway env vars
const ZEP_GRAPH_NAME = process.env.ZEP_GRAPH_NAME || 'fractional-jobs-graph';

// Categorize a fact into ontological type
function categorize(fact: string, edgeName?: string): 'role' | 'location' | 'skill' | 'interest' | 'experience' | 'fact' {
  const lower = fact.toLowerCase();
  const edge = (edgeName || '').toLowerCase();

  // Role keywords
  if (['cto', 'cfo', 'cmo', 'coo', 'chro', 'cpo', 'cro', 'ciso', 'chief'].some(k => lower.includes(k))) {
    return 'role';
  }
  // Location keywords
  if (['london', 'manchester', 'birmingham', 'remote', 'uk', 'hybrid'].some(k => lower.includes(k))) {
    return 'location';
  }
  // Skill/experience keywords
  if (['experience', 'years', 'background', 'worked', 'led', 'managed'].some(k => lower.includes(k))) {
    return 'experience';
  }
  // Interest keywords
  if (['interested', 'looking for', 'wants', 'prefers', 'likes'].some(k => lower.includes(k)) || edge.includes('interest')) {
    return 'interest';
  }
  // Skill keywords
  if (['skill', 'expert', 'proficient', 'specializ'].some(k => lower.includes(k))) {
    return 'skill';
  }
  return 'fact';
}

// Clean up fact text for display
function cleanFact(fact: string): string {
  return fact
    .replace(/^(the user |user |they |he |she )/i, '')
    .replace(/^(is |are |has |have |wants |prefers )/i, '')
    .trim();
}

export async function GET(request: NextRequest) {
  const userId = request.nextUrl.searchParams.get('userId');

  if (!userId || !ZEP_API_KEY) {
    return NextResponse.json({ context: '', facts: [], entities: { roles: [], locations: [], interests: [], experiences: [] } });
  }

  try {
    // Fetch user's memory from Zep knowledge graph
    const response = await fetch('https://api.getzep.com/api/v2/graph/search', {
      method: 'POST',
      headers: {
        'Authorization': `Api-Key ${ZEP_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        query: 'user preferences interests roles locations experience jobs',
        limit: 15,
        scope: 'edges',
      }),
    });

    if (!response.ok) {
      console.error('[Zep] Graph search failed:', response.status);
      return NextResponse.json({ context: '', facts: [], entities: { roles: [], locations: [], interests: [], experiences: [] } });
    }

    const data = await response.json();
    const edges = data.edges || [];

    // Extract and categorize facts
    const categorizedFacts: Array<{ fact: string; type: string; clean: string }> = [];
    const entities = {
      roles: [] as string[],
      locations: [] as string[],
      interests: [] as string[],
      experiences: [] as string[],
    };

    for (const edge of edges) {
      if (!edge.fact) continue;

      const type = categorize(edge.fact, edge.name);
      const clean = cleanFact(edge.fact);

      categorizedFacts.push({ fact: edge.fact, type, clean });

      // Collect unique entities by type
      if (type === 'role' && !entities.roles.includes(clean)) {
        entities.roles.push(clean);
      } else if (type === 'location' && !entities.locations.includes(clean)) {
        entities.locations.push(clean);
      } else if (type === 'interest' && !entities.interests.includes(clean)) {
        entities.interests.push(clean);
      } else if (type === 'experience' && !entities.experiences.includes(clean)) {
        entities.experiences.push(clean);
      }
    }

    // Build context string grouped by type
    const contextParts: string[] = [];

    if (entities.roles.length) {
      contextParts.push(`Roles: ${entities.roles.join(', ')}`);
    }
    if (entities.locations.length) {
      contextParts.push(`Locations: ${entities.locations.join(', ')}`);
    }
    if (entities.interests.length) {
      contextParts.push(`Interests: ${entities.interests.join(', ')}`);
    }
    if (entities.experiences.length) {
      contextParts.push(`Experience: ${entities.experiences.join(', ')}`);
    }

    const context = contextParts.length > 0
      ? contextParts.join('\n')
      : '';

    return NextResponse.json({
      context,
      facts: categorizedFacts,
      entities,
    });
  } catch (error) {
    console.error('[Zep] Error:', error);
    return NextResponse.json({ context: '', facts: [], entities: { roles: [], locations: [], interests: [], experiences: [] } });
  }
}
