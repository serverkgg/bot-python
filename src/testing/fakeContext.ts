import type { Bridge } from "@serverkgg/bridge";

export const SERVER_CODE = "bt7k2m9q4x";

export interface FakeContextOptions {
	variables?: Record<string, string>;
	secrets?: Record<string, string>;
	ports?: Record<string, number>;
	files?: Record<string, string>;
	memoryMb?: number;
	running?: boolean;
}

export interface FakeFollower {
	pattern: RegExp;
	onMatch(match: RegExpMatchArray): void;
}

export interface FakeEmit {
	event: string;
	payload: Bridge.Values | null;
}

export const fakeContext = (options: FakeContextOptions = {}) => {
	const variables: Record<string, string> = {
		...options.variables,
	};
	const secrets: Record<string, string> = {
		...options.secrets,
	};
	const ports: Record<string, number> = {
		...options.ports,
	};
	const stored = new Map(Object.entries(options.files ?? {}));
	const followers: FakeFollower[] = [];
	const emitted: FakeEmit[] = [];

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
		port(key: string) {
			const port = ports[key];

			if (port === undefined) {
				throw new Error(`no port named ${key}`);
			}

			return port;
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
		emit(event: string, payload?: Bridge.Values) {
			emitted.push({
				event,
				payload: payload ?? null,
			});
		},
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
		emitted,
		print,
	};
};
