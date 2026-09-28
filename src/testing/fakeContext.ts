import type { Bridge } from "@serverkgg/bridge";

export const SERVER_CODE = "bt7k2m9q4x";

export interface FakeContextOptions {
	variables?: Record<string, string>;
	secrets?: Record<string, string>;
	files?: Record<string, string>;
	memoryMb?: number;
	running?: boolean;
}

export interface FakeFollower {
	pattern: RegExp;
	onMatch(match: RegExpMatchArray): void;
}

export const fakeContext = (options: FakeContextOptions = {}) => {
	const variables: Record<string, string> = {
		...options.variables,
	};
	const secrets: Record<string, string> = {
		...options.secrets,
	};
	const stored = new Map(Object.entries(options.files ?? {}));
	const followers: FakeFollower[] = [];

	const context = {
		server: {
			code: SERVER_CODE,
			memoryMb: options.memoryMb ?? 1024,
			cpuPercent: 100,
			running: options.running ?? false,
		},
		variable(key: string) {
			return variables[key] ?? null;
		},
		variables() {
			return variables;
		},
		secret(key: string) {
			return secrets[key] ?? null;
		},
		secrets() {
			return secrets;
		},
		files: {
			async exists(path: string) {
				return stored.has(path);
			},
			async read(path: string) {
				const content = stored.get(path);

				if (content === undefined) {
					throw new Error(`no file at ${path}`);
				}

				return content;
			},
			async write(path: string, content: string) {
				stored.set(path, content);
			},
		},
		logs: {
			async tail() {
				return [];
			},
			async watch() {
				return null;
			},
			follow(pattern: RegExp, onMatch: (match: RegExpMatchArray) => void) {
				const follower = {
					pattern,
					onMatch,
				};

				followers.push(follower);

				return () => {
					followers.splice(followers.indexOf(follower), 1);
				};
			},
		},
		log: Object.assign(() => undefined, {
			warn: () => undefined,
			error: () => undefined,
		}),
	} as unknown as Bridge.Context;

	const print = (line: string) => {
		for (const follower of [
			...followers,
		]) {
			const match = line.match(follower.pattern);

			if (match) {
				follower.onMatch(match);
			}
		}
	};

	return {
		context,
		variables,
		secrets,
		stored,
		followers,
		print,
	};
};
