#!/usr/bin/perl
# main program

=pod
Documentation block v2
=cut

sub greet {
    my ($Name) = @_;
    return "hello $name";
}

print greet("world");
